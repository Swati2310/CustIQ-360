"""
agents/graph.py
---------------
LangGraph multi-agent orchestration for CustIQ 360°.

Architecture:
  START
    └─► router_node  (classify intent)
          ├─ lookup      ──► query_node      ──► END
          ├─ query       ──► query_node      ──► END
          ├─ simulate    ──► simulator_node  ──► END
          ├─ recommend   ──► recommender_node ──► compliance_node ──► END
          ├─ compliance  ──► compliance_node ──► END
          ├─ alert       ──► alert_node      ──► END
          └─ (fallback)  ──► fallback_node   ──► END
"""

from __future__ import annotations

import json
import os
import traceback
from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

# LangGraph imports
from langgraph.graph import END, StateGraph

from agents.prompts import (
    ALERT_PROMPT,
    COMPLIANCE_PROMPT,
    QUERY_ENGINE_PROMPT,
    RECOMMENDER_PROMPT,
    SIMULATOR_PROMPT,
)
from agents.router import classify_intent
from agents.tools import (
    _load_products,
    calculate_emi,
    calculate_fd_maturity,
    get_customer_kyc,
    get_customer_loans,
    get_customer_profile,
    get_customer_wealth,
    search_products,
)
from config import settings

# ---------------------------------------------------------------------------
# State definition
# ---------------------------------------------------------------------------


class AgentState(TypedDict, total=False):
    """Shared mutable state passed between every node in the graph."""

    messages: List[Any]           # Full conversation history (LangChain message objects)
    customer_id: Optional[str]    # Active customer ID, may be None for generic questions
    intent: str                   # Classified intent label
    context: str                  # Retrieved context / tool outputs
    response: str                 # Final natural-language response from the active agent
    error: Optional[str]          # Set if a node encounters an unrecoverable error


# ---------------------------------------------------------------------------
# LLM factory — created lazily, shared across nodes in the same request
# ---------------------------------------------------------------------------

_llm: Optional[Any] = None


def _get_llm():
    """Return a cached ChatGoogleGenerativeAI instance; create if not yet initialised."""
    global _llm
    if _llm is not None:
        return _llm
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore

        _llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_CHAT_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.1,
        )
        return _llm
    except Exception as exc:
        raise RuntimeError(f"Failed to create ChatGoogleGenerativeAI instance: {exc}") from exc


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _safe_invoke(llm, messages: List[Any]) -> str:
    """Invoke the LLM and return the text content, or an error string."""
    try:
        response = llm.invoke(messages)
        if hasattr(response, "content"):
            return str(response.content)
        return str(response)
    except Exception as exc:
        return f"[LLM error] {exc}"


def _tool_output(tool_func, **kwargs) -> str:
    """Call a LangChain tool safely and return its string output."""
    try:
        return tool_func.invoke(kwargs)
    except Exception as exc:
        return json.dumps({"error": str(exc)})


# ---------------------------------------------------------------------------
# Node implementations
# ---------------------------------------------------------------------------


def router_node(state: AgentState) -> AgentState:
    """Classify the latest user message and store the intent in state."""
    try:
        llm = _get_llm()
        messages = state.get("messages", [])
        if not messages:
            return {**state, "intent": "query", "error": None}

        # Use the last human message for classification
        last_human = ""
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                last_human = str(msg.content)
                break

        intent = classify_intent(last_human, llm)
        return {**state, "intent": intent, "error": None}

    except Exception as exc:
        print(f"[router_node] error: {exc}")
        return {**state, "intent": "query", "error": str(exc)}


def query_node(state: AgentState) -> AgentState:
    """Answer lookup / query questions using customer data as context."""
    try:
        llm = _get_llm()
        customer_id = state.get("customer_id")
        messages = state.get("messages", [])

        # Build context from customer profile if a customer is in scope
        context_parts: List[str] = []
        if customer_id:
            profile = _tool_output(get_customer_profile, customer_id=customer_id)
            context_parts.append(f"Customer Profile:\n{profile}")

        context = "\n\n".join(context_parts) if context_parts else "No customer context available."

        system_msg = SystemMessage(
            content=QUERY_ENGINE_PROMPT.format(context=context)
        )
        response_text = _safe_invoke(llm, [system_msg] + messages)

        return {**state, "context": context, "response": response_text, "error": None}

    except Exception as exc:
        tb = traceback.format_exc()
        print(f"[query_node] error:\n{tb}")
        return {
            **state,
            "response": "I encountered an error retrieving the information. Please try again.",
            "error": str(exc),
        }


def recommender_node(state: AgentState) -> AgentState:
    """Generate cross-sell product recommendations for a customer."""
    try:
        llm = _get_llm()
        customer_id = state.get("customer_id")

        if not customer_id:
            return {
                **state,
                "response": "Please specify a customer ID to generate recommendations.",
                "error": "No customer_id provided.",
            }

        profile = _tool_output(get_customer_profile, customer_id=customer_id)
        products = json.dumps(_load_products(), indent=2)

        system_msg = SystemMessage(
            content=RECOMMENDER_PROMPT.format(
                customer_profile=profile,
                products=products,
            )
        )
        messages = state.get("messages", [])
        response_text = _safe_invoke(llm, [system_msg] + messages)

        return {
            **state,
            "context": profile,
            "response": response_text,
            "error": None,
        }

    except Exception as exc:
        tb = traceback.format_exc()
        print(f"[recommender_node] error:\n{tb}")
        return {
            **state,
            "response": "Unable to generate recommendations at this time.",
            "error": str(exc),
        }


def simulator_node(state: AgentState) -> AgentState:
    """Handle EMI, FD maturity, and other financial calculations."""
    try:
        llm = _get_llm()
        messages = state.get("messages", [])

        # Extract the user's last message to understand what to calculate
        last_human = ""
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                last_human = str(msg.content)
                break

        # Provide pre-computed tool results as context so the LLM can explain them
        calc_context = (
            f"User request: {last_human}\n\n"
            "Available calculation tools:\n"
            "- calculate_emi(principal, rate_percent, tenure_months)\n"
            "- calculate_fd_maturity(principal, rate_percent, tenure_days)\n\n"
            "Parse the numbers from the user request and explain the calculation."
        )

        system_msg = SystemMessage(
            content=SIMULATOR_PROMPT.format(calculation_context=calc_context)
        )
        response_text = _safe_invoke(llm, [system_msg] + messages)

        return {
            **state,
            "context": calc_context,
            "response": response_text,
            "error": None,
        }

    except Exception as exc:
        tb = traceback.format_exc()
        print(f"[simulator_node] error:\n{tb}")
        return {
            **state,
            "response": "Unable to perform the calculation at this time.",
            "error": str(exc),
        }


def compliance_node(state: AgentState) -> AgentState:
    """Validate customer eligibility for a product / check KYC compliance."""
    try:
        llm = _get_llm()
        customer_id = state.get("customer_id")
        messages = state.get("messages", [])

        # Build context
        profile = ""
        if customer_id:
            profile = _tool_output(get_customer_profile, customer_id=customer_id)

        # For recommender → compliance pipeline, only validate the recommended products
        prior_response = state.get("response", "")

        if state.get("intent") == "recommend" and prior_response:
            # Pass only the prior recommendations — not the full 15-product catalogue
            product_details = (
                f"The following products were recommended for this customer:\n\n{prior_response}\n\n"
                "Validate eligibility only for the products listed above. Do NOT check products not mentioned."
            )
        else:
            products_context = json.dumps(_load_products(), indent=2)
            product_details = f"Product catalogue:\n{products_context}"

        system_msg = SystemMessage(
            content=COMPLIANCE_PROMPT.format(
                customer_profile=profile or "No customer profile provided.",
                product_details=product_details,
            )
        )
        response_text = _safe_invoke(llm, [system_msg] + messages)

        # Merge compliance result with prior response if coming from recommender
        if state.get("intent") == "recommend" and prior_response:
            combined = (
                f"{prior_response}\n\n---\n**Compliance Check:**\n{response_text}"
            )
        else:
            combined = response_text

        return {
            **state,
            "context": profile,
            "response": combined,
            "error": None,
        }

    except Exception as exc:
        tb = traceback.format_exc()
        print(f"[compliance_node] error:\n{tb}")
        return {
            **state,
            "response": "Unable to perform compliance validation at this time.",
            "error": str(exc),
        }


def _alerts_to_narrative(raw: str) -> str:
    """Convert the alert engine's JSON array into a readable natural-language answer."""
    cleaned = raw.strip().strip("```json").strip("```").strip()
    try:
        alerts = json.loads(cleaned)
    except json.JSONDecodeError:
        return raw  # already natural language

    if not isinstance(alerts, list):
        return raw

    if not alerts:
        return (
            "✅ No active alerts for this customer right now. "
            "All KYC documents are valid, no FDs are maturing within 60 days, "
            "no overdue loans, and all accounts are in good standing."
        )

    severity_emoji = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}
    lines = [f"⚠️ Found **{len(alerts)}** alert(s):\n"]
    for a in alerts:
        emoji = severity_emoji.get(a.get("severity", ""), "⚪")
        alert_type = a.get("alert_type", "ALERT").replace("_", " ").title()
        severity = a.get("severity", "")
        message = a.get("message", "")
        action = a.get("recommended_action", "")
        lines.append(f"{emoji} **{alert_type}** ({severity})")
        if message:
            lines.append(f"   {message}")
        if action:
            lines.append(f"   👉 *{action}*")
        lines.append("")
    return "\n".join(lines)


def alert_node(state: AgentState) -> AgentState:
    """Generate proactive alert summaries for a customer or all customers."""
    try:
        llm = _get_llm()
        customer_id = state.get("customer_id")
        messages = state.get("messages", [])

        if customer_id:
            customer_data = _tool_output(get_customer_profile, customer_id=customer_id)
        else:
            customer_data = "No specific customer selected. Scan all available data."

        system_msg = SystemMessage(
            content=ALERT_PROMPT.format(customer_data=customer_data)
        )
        raw_response = _safe_invoke(llm, [system_msg] + messages)
        response_text = _alerts_to_narrative(raw_response)

        return {**state, "context": customer_data, "response": response_text, "error": None}

    except Exception as exc:
        tb = traceback.format_exc()
        print(f"[alert_node] error:\n{tb}")
        return {**state, "response": "Unable to generate alerts at this time.", "error": str(exc)}


def fallback_node(state: AgentState) -> AgentState:
    """Handle unknown intents or hard errors gracefully."""
    error = state.get("error")
    intent = state.get("intent", "unknown")
    msg = (
        f"I'm sorry, I couldn't process your request (intent: {intent}). "
        "Please try rephrasing your question or contact support."
    )
    if error:
        msg += f"\n\nTechnical detail: {error}"
    return {**state, "response": msg}


# ---------------------------------------------------------------------------
# Routing function
# ---------------------------------------------------------------------------


def _route_by_intent(state: AgentState) -> str:
    """Conditional edge: map intent label to the next node name."""
    intent = state.get("intent", "query")
    routing_map = {
        "lookup": "query_node",
        "query": "query_node",
        "simulate": "simulator_node",
        "recommend": "recommender_node",
        "compliance": "compliance_node",
        "alert": "alert_node",
    }
    return routing_map.get(intent, "fallback_node")


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

_compiled_graph: Optional[Any] = None


def create_graph():
    """Build and compile the LangGraph StateGraph. Returns the compiled graph."""
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("router_node", router_node)
    graph.add_node("query_node", query_node)
    graph.add_node("simulator_node", simulator_node)
    graph.add_node("recommender_node", recommender_node)
    graph.add_node("compliance_node", compliance_node)
    graph.add_node("alert_node", alert_node)
    graph.add_node("fallback_node", fallback_node)

    # Entry point
    graph.set_entry_point("router_node")

    # Conditional routing from router → specialised nodes
    graph.add_conditional_edges(
        "router_node",
        _route_by_intent,
        {
            "query_node": "query_node",
            "simulator_node": "simulator_node",
            "recommender_node": "recommender_node",
            "compliance_node": "compliance_node",
            "alert_node": "alert_node",
            "fallback_node": "fallback_node",
        },
    )

    # recommender → compliance → END (two-step pipeline)
    graph.add_edge("recommender_node", "compliance_node")
    graph.add_edge("compliance_node", END)

    # All other specialised nodes → END
    graph.add_edge("query_node", END)
    graph.add_edge("simulator_node", END)
    graph.add_edge("alert_node", END)
    graph.add_edge("fallback_node", END)

    return graph.compile()


def _get_graph():
    """Lazy singleton: compile the graph on first call."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = create_graph()
    return _compiled_graph


# ---------------------------------------------------------------------------
# Public async interface
# ---------------------------------------------------------------------------


async def ainvoke_graph(
    user_message: str,
    customer_id: Optional[str] = None,
    history: Optional[List[Any]] = None,
) -> Dict[str, Any]:
    """
    Async entry point for the LangGraph pipeline.

    Args:
        user_message: The latest message from the user.
        customer_id: Optional active customer ID.
        history: Prior conversation messages (list of LangChain message objects).

    Returns:
        A dict with keys: response, intent, error.
    """
    if history is None:
        history = []

    # Append the new user message to the history
    messages = list(history) + [HumanMessage(content=user_message)]

    initial_state: AgentState = {
        "messages": messages,
        "customer_id": customer_id,
        "intent": "",
        "context": "",
        "response": "",
        "error": None,
    }

    try:
        graph = _get_graph()
        final_state = await graph.ainvoke(initial_state)
        return {
            "response": final_state.get("response", "No response generated."),
            "intent": final_state.get("intent", "unknown"),
            "error": final_state.get("error"),
        }
    except RuntimeError as exc:
        # Gemini API not reachable or key invalid
        error_msg = str(exc)
        if "connection" in error_msg.lower() or "refused" in error_msg.lower() or "api" in error_msg.lower():
            return {
                "response": (
                    "The AI service (Gemini) is not reachable. "
                    "Please check your GEMINI_API_KEY and network connection."
                ),
                "intent": "unknown",
                "error": error_msg,
            }
        return {
            "response": f"An internal error occurred: {exc}",
            "intent": "unknown",
            "error": error_msg,
        }
    except Exception as exc:
        tb = traceback.format_exc()
        print(f"[ainvoke_graph] unexpected error:\n{tb}")
        return {
            "response": "An unexpected error occurred. Please try again.",
            "intent": "unknown",
            "error": str(exc),
        }
