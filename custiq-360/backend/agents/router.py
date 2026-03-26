"""
agents/router.py
----------------
Intent classification router for the CustIQ 360° LangGraph pipeline.

Accepts a user message and an LLM instance and returns one of the
pre-defined intent labels used to route control to the correct agent node.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from agents.prompts import ROUTER_PROMPT

# Valid intent labels — used for validation / fallback
VALID_INTENTS = frozenset(
    {"lookup", "query", "simulate", "recommend", "compliance", "alert"}
)

_DEFAULT_INTENT = "query"


def classify_intent(user_message: str, llm) -> str:
    """
    Use the LLM to classify the user's intent into one of the predefined labels.

    Args:
        user_message: The raw message from the user / relationship manager.
        llm: A LangChain chat model instance (e.g. ChatOllama).

    Returns:
        One of: "lookup", "query", "simulate", "recommend", "compliance", "alert".
        Falls back to "query" on any error or unrecognised output.
    """
    try:
        messages = [
            SystemMessage(content=ROUTER_PROMPT),
            HumanMessage(content=user_message),
        ]
        response = llm.invoke(messages)
        # Extract text content — handle both str and object responses
        if hasattr(response, "content"):
            raw = str(response.content).strip().lower()
        else:
            raw = str(response).strip().lower()

        # Strip punctuation that some models append
        raw = raw.strip(".,;:!? \n\t\"'")

        # Return if valid, otherwise fall back to "query"
        if raw in VALID_INTENTS:
            return raw

        # Try to extract a valid label from a longer response
        for intent in VALID_INTENTS:
            if intent in raw:
                return intent

        return _DEFAULT_INTENT

    except Exception as exc:
        print(f"[router] classify_intent error: {exc}")
        return _DEFAULT_INTENT
