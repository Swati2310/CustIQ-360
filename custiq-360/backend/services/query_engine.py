"""
services/query_engine.py
------------------------
Conversational Query Engine service for CustIQ 360°.

Wraps the LangGraph pipeline and exposes a simple async chat() interface
used by the API layer.  The retriever parameter is reserved for future
FAISS/RAG integration (Phase 2 hook-in).
"""

from __future__ import annotations

import traceback
from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage, HumanMessage


class QueryEngine:
    """
    Thin service layer that bridges the FastAPI routes and the LangGraph graph.

    Args:
        graph: A compiled LangGraph graph (from agents.graph.create_graph()).
        retriever: Optional FAISS / vector-store retriever for RAG context
                   (not yet wired in Phase 3 — accepted for forward compatibility).
    """

    def __init__(self, graph: Any, retriever: Optional[Any] = None) -> None:
        self._graph = graph
        self._retriever = retriever  # reserved for Phase 2 RAG integration

    # ── Public interface ───────────────────────────────────────────────────

    async def chat(
        self,
        message: str,
        customer_id: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Process a single conversational turn and return the agent's reply.

        Args:
            message: The user's latest natural-language message.
            customer_id: Optional ID of the customer currently in context.
            history: Prior conversation turns as a list of dicts:
                     [{"role": "user" | "assistant", "content": "..."}]

        Returns:
            {
                "response": str,   — the agent's reply
                "intent":   str,   — classified intent label
                "sources":  list,  — list of source references (empty in Phase 3)
            }
        """
        if history is None:
            history = []

        # Convert dict history to LangChain message objects
        lc_history = self._convert_history(history)

        try:
            from agents.graph import ainvoke_graph  # avoid circular import at module level

            result = await ainvoke_graph(
                user_message=message,
                customer_id=customer_id,
                history=lc_history,
            )

            return {
                "response": result.get("response", ""),
                "intent": result.get("intent", "unknown"),
                "sources": [],  # populated in Phase 4 with RAG document sources
            }

        except Exception as exc:
            tb = traceback.format_exc()
            print(f"[QueryEngine.chat] error:\n{tb}")
            return {
                "response": (
                    "I'm sorry, I encountered an error processing your request. "
                    "Please try again or contact support."
                ),
                "intent": "unknown",
                "sources": [],
            }

    # ── Private helpers ────────────────────────────────────────────────────

    @staticmethod
    def _convert_history(
        history: List[Dict[str, str]],
    ) -> List[Any]:
        """
        Convert a list of {"role": ..., "content": ...} dicts into
        LangChain HumanMessage / AIMessage objects.
        """
        lc_messages = []
        for turn in history:
            role = turn.get("role", "user").lower()
            content = turn.get("content", "")
            if role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role in ("assistant", "ai"):
                lc_messages.append(AIMessage(content=content))
            # Ignore unknown roles silently
        return lc_messages
