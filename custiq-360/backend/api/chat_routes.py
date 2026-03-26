"""
api/chat_routes.py
------------------
FastAPI router for Phase 3 LLM agent endpoints in CustIQ 360°.

Endpoints:
  POST /api/chat                        — conversational AI agent (SSE streaming)
  GET  /api/recommendations/{customer_id} — cross-sell recommendations
  GET  /api/alerts                      — all active proactive alerts
"""

from __future__ import annotations

import asyncio
import json
import traceback
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services.alerts import AlertEngine
from services.compliance import ComplianceAgent
from services.recommender import Recommender

router = APIRouter(prefix="/api", tags=["agents"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    message: str
    customer_id: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = []


class RecommendationItem(BaseModel):
    product_name: str
    reason: str
    compliance_status: str
    priority: str


class AlertItem(BaseModel):
    alert_type: str
    severity: str
    customer_id: str
    customer_name: str
    message: str
    recommended_action: str
    metadata: Dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Dependency helpers
# ---------------------------------------------------------------------------


def _get_aggregator(request: Request):
    """Retrieve the shared CustomerAggregator from app state."""
    return request.app.state.aggregator


def _get_query_engine(request: Request):
    """
    Retrieve the QueryEngine from app state (set during lifespan startup).
    Returns None if not yet initialised (Ollama not running).
    """
    return getattr(request.app.state, "query_engine", None)


# ---------------------------------------------------------------------------
# POST /api/chat — Streaming SSE conversational endpoint
# ---------------------------------------------------------------------------


@router.post(
    "/chat",
    summary="Conversational AI agent (streaming SSE)",
    description=(
        "Send a message to the CustIQ 360° LangGraph agent. "
        "Optionally provide a customer_id to scope the conversation. "
        "Response is streamed as Server-Sent Events (text/event-stream)."
    ),
)
async def chat(
    body: ChatRequest,
    request: Request,
) -> StreamingResponse:
    """
    Stream the AI agent's response using Server-Sent Events.

    Each SSE event carries a JSON chunk:
      data: {"type": "chunk", "content": "..."}\n\n
      data: {"type": "done", "intent": "...", "sources": []}\n\n
      data: {"type": "error", "content": "..."}\n\n
    """

    async def event_generator():
        try:
            query_engine = _get_query_engine(request)

            if query_engine is None:
                # Lazy initialisation: build the engine on first request
                from agents.graph import create_graph
                from services.query_engine import QueryEngine

                try:
                    graph = create_graph()
                    query_engine = QueryEngine(graph=graph)
                    request.app.state.query_engine = query_engine
                except Exception as exc:
                    error_payload = json.dumps(
                        {"type": "error", "content": f"AI service initialisation failed: {exc}"}
                    )
                    yield f"data: {error_payload}\n\n"
                    return

            # Run the agent (non-blocking)
            result = await query_engine.chat(
                message=body.message,
                customer_id=body.customer_id,
                history=body.history or [],
            )

            response_text: str = result.get("response", "")
            intent: str = result.get("intent", "unknown")
            sources: list = result.get("sources", [])

            # Stream the response word-by-word to simulate real-time output
            words = response_text.split(" ")
            buffer = []
            for i, word in enumerate(words):
                buffer.append(word)
                # Flush every 5 words or at the end
                if len(buffer) >= 5 or i == len(words) - 1:
                    chunk = " ".join(buffer)
                    if i < len(words) - 1:
                        chunk += " "
                    payload = json.dumps({"type": "chunk", "content": chunk})
                    yield f"data: {payload}\n\n"
                    buffer = []
                    await asyncio.sleep(0)  # yield control to event loop

            # Final done event
            done_payload = json.dumps(
                {"type": "done", "intent": intent, "sources": sources}
            )
            yield f"data: {done_payload}\n\n"

        except asyncio.CancelledError:
            # Client disconnected — clean exit
            return
        except Exception as exc:
            tb = traceback.format_exc()
            print(f"[chat] streaming error:\n{tb}")
            error_payload = json.dumps(
                {"type": "error", "content": f"An error occurred: {exc}"}
            )
            yield f"data: {error_payload}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable Nginx buffering for SSE
        },
    )


# ---------------------------------------------------------------------------
# GET /api/recommendations/{customer_id}
# ---------------------------------------------------------------------------


@router.get(
    "/recommendations/{customer_id}",
    response_model=List[RecommendationItem],
    summary="Get cross-sell recommendations for a customer",
    description=(
        "Returns a prioritised list of product recommendations for the given customer "
        "based on their profile, segment, and current holdings. "
        "Each recommendation includes a reason and compliance status."
    ),
)
def get_recommendations(
    customer_id: str,
    request: Request,
) -> List[RecommendationItem]:
    aggregator = _get_aggregator(request)

    # Verify customer exists
    customer = aggregator.get_customer_by_id(customer_id)
    if customer is None:
        raise HTTPException(
            status_code=404,
            detail=f"Customer '{customer_id}' not found.",
        )

    # Attempt to wire up LLM (optional — falls back to rule-based if unavailable)
    llm = None
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from config import settings

        llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_CHAT_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.1,
        )
    except Exception:
        pass  # Rule-based fallback will be used

    try:
        recommender = Recommender(aggregator=aggregator, llm=llm)
        recommendations = recommender.get_recommendations(customer_id)
        return [RecommendationItem(**r) for r in recommendations]
    except Exception as exc:
        tb = traceback.format_exc()
        print(f"[recommendations] error for {customer_id}:\n{tb}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate recommendations: {exc}",
        )


# ---------------------------------------------------------------------------
# GET /api/alerts
# ---------------------------------------------------------------------------


@router.get(
    "/alerts",
    response_model=List[AlertItem],
    summary="Get all active proactive alerts",
    description=(
        "Scans all customers and returns proactive alerts for relationship managers: "
        "expiring KYC documents, maturing FDs, dormant accounts, overdue loans, "
        "and cross-sell opportunities. Sorted by severity (Critical first)."
    ),
)
def get_alerts(request: Request) -> List[AlertItem]:
    aggregator = _get_aggregator(request)

    try:
        engine = AlertEngine(aggregator=aggregator)
        alerts = engine.generate_alerts()
        return [AlertItem(**a.to_dict()) for a in alerts]
    except Exception as exc:
        tb = traceback.format_exc()
        print(f"[alerts] error:\n{tb}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate alerts: {exc}",
        )
