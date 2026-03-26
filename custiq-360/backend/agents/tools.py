"""
agents/tools.py
---------------
LangChain tool definitions for the CustIQ 360° LangGraph agents.

Tools interact with the CustomerAggregator (via a module-level reference set
at startup) and perform pure financial calculations.
"""

from __future__ import annotations

import json
import math
import os
from typing import Any, Dict, List, Optional

from langchain_core.tools import tool

# ---------------------------------------------------------------------------
# Module-level aggregator reference
# ---------------------------------------------------------------------------
# This is set from main.py / lifespan after the aggregator is created so that
# tools can access customer data without needing dependency injection.

_aggregator: Optional[Any] = None  # type: CustomerAggregator at runtime


def set_aggregator(aggregator: Any) -> None:
    """Inject the shared CustomerAggregator into this module."""
    global _aggregator
    _aggregator = aggregator


# ---------------------------------------------------------------------------
# Data path for products.json
# ---------------------------------------------------------------------------

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
_PRODUCTS_JSON = os.path.join(_DATA_DIR, "products.json")


def _load_products() -> List[Dict[str, Any]]:
    """Load products.json and return the list."""
    try:
        with open(_PRODUCTS_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


# ---------------------------------------------------------------------------
# Customer data tools
# ---------------------------------------------------------------------------


@tool
def get_customer_profile(customer_id: str) -> str:
    """
    Retrieve the complete 360° profile for a customer by their customer_id.
    Returns a JSON string containing all customer data: accounts, loans,
    wealth holdings, and KYC information.
    """
    if _aggregator is None:
        return json.dumps({"error": "Data store not initialised."})
    customer = _aggregator.get_customer_by_id(customer_id)
    if customer is None:
        return json.dumps({"error": f"Customer '{customer_id}' not found."})
    try:
        return customer.model_dump_json(indent=2)
    except Exception as exc:
        return json.dumps({"error": str(exc)})


@tool
def get_customer_accounts(customer_id: str) -> str:
    """
    Retrieve all bank accounts (Savings, Current, NRI) for a customer,
    including recent transactions and current balances in Indian Rupees (₹).
    Returns a JSON string.
    """
    if _aggregator is None:
        return json.dumps({"error": "Data store not initialised."})
    accounts = _aggregator.get_accounts(customer_id)
    if accounts is None:
        return json.dumps({"error": f"Customer '{customer_id}' not found."})
    try:
        return json.dumps([a.model_dump() for a in accounts], indent=2, default=str)
    except Exception as exc:
        return json.dumps({"error": str(exc)})


@tool
def get_customer_loans(customer_id: str) -> str:
    """
    Retrieve all loan records for a customer — Home Loan, Personal Loan,
    Car Loan, Education Loan — including outstanding principal, EMI, and status.
    All amounts are in Indian Rupees (₹). Returns a JSON string.
    """
    if _aggregator is None:
        return json.dumps({"error": "Data store not initialised."})
    loans = _aggregator.get_loans(customer_id)
    if loans is None:
        return json.dumps({"error": f"Customer '{customer_id}' not found."})
    try:
        return json.dumps([l.model_dump() for l in loans], indent=2, default=str)
    except Exception as exc:
        return json.dumps({"error": str(exc)})


@tool
def get_customer_wealth(customer_id: str) -> str:
    """
    Retrieve all wealth holdings for a customer — Fixed Deposits, Mutual Funds,
    Insurance policies, PPF accounts — including invested amounts and maturity dates.
    All amounts are in Indian Rupees (₹). Returns a JSON string.
    """
    if _aggregator is None:
        return json.dumps({"error": "Data store not initialised."})
    wealth = _aggregator.get_wealth(customer_id)
    if wealth is None:
        return json.dumps({"error": f"Customer '{customer_id}' not found."})
    try:
        return json.dumps([w.model_dump() for w in wealth], indent=2, default=str)
    except Exception as exc:
        return json.dumps({"error": str(exc)})


@tool
def get_customer_kyc(customer_id: str) -> str:
    """
    Retrieve KYC details for a customer — Aadhaar, PAN, address proof verification
    status, document expiry dates, and risk category (Low/Medium/High).
    Returns a JSON string.
    """
    if _aggregator is None:
        return json.dumps({"error": "Data store not initialised."})
    kyc = _aggregator.get_kyc(customer_id)
    if kyc is None:
        return json.dumps({"error": f"Customer '{customer_id}' not found."})
    try:
        return kyc.model_dump_json(indent=2)
    except Exception as exc:
        return json.dumps({"error": str(exc)})


# ---------------------------------------------------------------------------
# Financial calculation tools
# ---------------------------------------------------------------------------


@tool
def calculate_emi(principal: float, rate_percent: float, tenure_months: int) -> str:
    """
    Calculate the monthly EMI (Equated Monthly Instalment) for a loan using the
    standard reducing-balance formula used by Indian banks.

    Args:
        principal: Loan principal amount in Indian Rupees (₹).
        rate_percent: Annual interest rate as a percentage (e.g., 8.5 for 8.5%).
        tenure_months: Loan tenure in months (e.g., 240 for 20 years).

    Returns a JSON string with: emi, total_interest, total_payment (all in ₹).
    """
    try:
        if principal <= 0:
            return json.dumps({"error": "Principal must be greater than zero."})
        if rate_percent < 0:
            return json.dumps({"error": "Interest rate cannot be negative."})
        if tenure_months <= 0:
            return json.dumps({"error": "Tenure must be at least 1 month."})

        monthly_rate = rate_percent / 100 / 12

        if monthly_rate == 0:
            # Zero-interest loan
            emi = round(principal / tenure_months, 2)
            total_interest = 0.0
        else:
            factor = (1 + monthly_rate) ** tenure_months
            emi = round(principal * monthly_rate * factor / (factor - 1), 2)
            total_interest = round(emi * tenure_months - principal, 2)

        total_payment = round(emi * tenure_months, 2)

        return json.dumps(
            {
                "principal": principal,
                "annual_rate_percent": rate_percent,
                "tenure_months": tenure_months,
                "monthly_emi": emi,
                "total_interest": total_interest,
                "total_payment": total_payment,
                "currency": "INR",
            },
            indent=2,
        )
    except Exception as exc:
        return json.dumps({"error": f"Calculation failed: {exc}"})


@tool
def calculate_fd_maturity(
    principal: float, rate_percent: float, tenure_days: int
) -> str:
    """
    Calculate the maturity value of a Fixed Deposit (FD) using quarterly
    compounding, which is the standard method used by Indian banks and the RBI.

    Args:
        principal: FD deposit amount in Indian Rupees (₹).
        rate_percent: Annual interest rate as a percentage (e.g., 7.25 for 7.25%).
        tenure_days: FD tenure in days (e.g., 365 for 1 year, 1825 for 5 years).

    Returns a JSON string with: maturity_value, interest_earned, effective_annual_yield.
    """
    try:
        if principal <= 0:
            return json.dumps({"error": "Principal must be greater than zero."})
        if rate_percent <= 0:
            return json.dumps({"error": "Interest rate must be greater than zero."})
        if tenure_days <= 0:
            return json.dumps({"error": "Tenure must be at least 1 day."})

        # Quarterly compounding: n = 4 compounding periods per year
        tenure_years = tenure_days / 365
        quarterly_rate = rate_percent / 100 / 4
        num_quarters = tenure_years * 4

        maturity_value = round(principal * (1 + quarterly_rate) ** num_quarters, 2)
        interest_earned = round(maturity_value - principal, 2)

        # Effective annual yield
        effective_yield = round(((1 + quarterly_rate) ** 4 - 1) * 100, 4)

        # TDS note (TDS applicable if interest > ₹40,000 per year for non-senior citizens)
        annual_interest_approx = round(interest_earned / tenure_years, 2) if tenure_years > 0 else interest_earned
        tds_applicable = annual_interest_approx > 40000

        return json.dumps(
            {
                "principal": principal,
                "annual_rate_percent": rate_percent,
                "tenure_days": tenure_days,
                "tenure_years": round(tenure_years, 2),
                "compounding": "quarterly",
                "maturity_value": maturity_value,
                "interest_earned": interest_earned,
                "effective_annual_yield_percent": effective_yield,
                "tds_applicable": tds_applicable,
                "tds_note": (
                    "TDS @ 10% applicable as estimated annual interest exceeds ₹40,000."
                    if tds_applicable
                    else "No TDS (annual interest below ₹40,000 threshold)."
                ),
                "currency": "INR",
            },
            indent=2,
        )
    except Exception as exc:
        return json.dumps({"error": f"Calculation failed: {exc}"})


# ---------------------------------------------------------------------------
# Product search tool
# ---------------------------------------------------------------------------


@tool
def search_products(query: str) -> str:
    """
    Search the CustIQ 360° banking product catalogue for products matching
    the query. Searches across product name, category, description, and features.
    Returns a JSON string containing matching products with their details,
    eligibility criteria (min_age, max_age, min_income in ₹), and interest rates.
    """
    try:
        products = _load_products()
        if not products:
            return json.dumps({"error": "Product catalogue not available."})

        query_lower = query.lower().strip()
        if not query_lower:
            return json.dumps(products, indent=2)

        matched = []
        for product in products:
            searchable = " ".join(
                [
                    product.get("name", ""),
                    product.get("category", ""),
                    product.get("description", ""),
                    " ".join(product.get("features", [])),
                ]
            ).lower()

            # Score by number of query words found
            words = query_lower.split()
            score = sum(1 for w in words if w in searchable)
            if score > 0:
                matched.append((score, product))

        # Sort by descending relevance score
        matched.sort(key=lambda x: x[0], reverse=True)
        results = [p for _, p in matched]

        if not results:
            return json.dumps(
                {
                    "message": f"No products found matching '{query}'.",
                    "available_categories": list(
                        {p.get("category", "") for p in products}
                    ),
                }
            )

        return json.dumps(results, indent=2)
    except Exception as exc:
        return json.dumps({"error": f"Product search failed: {exc}"})


# ---------------------------------------------------------------------------
# Exported tool list (convenience)
# ---------------------------------------------------------------------------

ALL_TOOLS = [
    get_customer_profile,
    get_customer_accounts,
    get_customer_loans,
    get_customer_wealth,
    get_customer_kyc,
    calculate_emi,
    calculate_fd_maturity,
    search_products,
]
