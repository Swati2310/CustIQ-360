from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure the backend directory itself is on sys.path so that absolute imports
# like `from models.customer import …` work when running with `uvicorn main:app`
# from inside the backend/ directory.
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from config import settings  # noqa: E402  (import after sys.path mutation)
from api.customer_routes import router  # noqa: E402
from api.search_routes import router as search_router  # noqa: E402
from api.document_routes import router as document_router  # noqa: E402
from api.chat_routes import router as chat_router  # noqa: E402
from api.simulator_routes import router as simulator_router  # noqa: E402
from api.alert_routes import router as alert_router  # noqa: E402
from services.aggregator import CustomerAggregator  # noqa: E402
from agents.tools import set_aggregator  # noqa: E402


# ── Application lifespan ───────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup / shutdown lifecycle handler.
    - Creates a CustomerAggregator and loads data from customers.json.
    - Stores the aggregator on app.state so it can be injected via Depends.
    """
    aggregator = CustomerAggregator()
    try:
        aggregator.load_customers()
    except FileNotFoundError as exc:
        # Non-fatal: the app can still start; routes will return empty results.
        print(f"[startup] WARNING — {exc}")

    app.state.aggregator = aggregator

    # Phase 3: wire aggregator into LangChain tools module for agent access
    set_aggregator(aggregator)
    # Mark query_engine as uninitialised — built lazily on first /api/chat request
    app.state.query_engine = None

    print("[startup] CustIQ 360° backend is ready.")
    yield
    # Teardown (nothing to clean up for in-memory store)
    print("[shutdown] CustIQ 360° backend shutting down.")


# ── App instantiation ──────────────────────────────────────────────────────

app = FastAPI(
    title="CustIQ 360° API",
    description=(
        "Customer Intelligence 360° platform — Phase 6: Integration & Deployment.\n\n"
        "Provides REST endpoints for customer profiles, accounts, loans, wealth holdings, "
        "and KYC data backed by an in-memory store loaded from JSON seed data.\n\n"
        "Phase 2 adds RAG-powered semantic search via FAISS + nomic-embed-text (Ollama).\n\n"
        "Phase 3 adds LangGraph multi-agent orchestration: conversational chat (SSE streaming), "
        "cross-sell recommendations, compliance validation, and proactive alerts.\n\n"
        "Phase 4 adds document extraction: upload ID proofs, salary slips, and property "
        "documents to receive structured JSON via LLaVA 13B vision model (Ollama) with "
        "pytesseract OCR as an automatic fallback.\n\n"
        "Phase 5 adds a financial simulator (EMI, FD, loan-scenario comparison) and "
        "proactive alert REST endpoints.\n\n"
        "Phase 6 packages the entire stack for Docker Compose deployment."
    ),
    version="6.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────

app.include_router(router)
app.include_router(search_router)
app.include_router(document_router)
app.include_router(chat_router)
app.include_router(simulator_router)
app.include_router(alert_router)


# ── Health check ───────────────────────────────────────────────────────────


@app.get(
    "/health",
    tags=["system"],
    summary="Health check",
    response_model=Dict[str, Any],
)
async def health_check() -> Dict[str, Any]:
    """
    Returns the application health status and basic configuration summary.
    Used by load balancers, Docker health checks, and monitoring tools.
    """
    aggregator: CustomerAggregator = app.state.aggregator
    return {
        "status": "ok",
        "service": "custiq-360-backend",
        "version": "6.0.0",
        "customers_loaded": aggregator.count(),
        "chat_model": settings.GEMINI_CHAT_MODEL,
        "embed_model": settings.GEMINI_EMBED_MODEL,
    }


# ── Dev server entrypoint ──────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[_BACKEND_DIR],
    )
