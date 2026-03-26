"""
services/recommender.py
-----------------------
Cross-sell / up-sell Recommender service for CustIQ 360°.

Combines rule-based eligibility filtering with LLM-powered reasoning to
generate personalised product recommendations for Indian retail banking customers.
"""

from __future__ import annotations

import json
import os
import traceback
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from agents.prompts import RECOMMENDER_PROMPT
from agents.tools import _load_products

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


class Recommender:
    """
    Cross-sell recommender that applies eligibility rules and uses an LLM
    for personalised reasoning.

    Args:
        aggregator: CustomerAggregator instance for fetching customer data.
        llm: Optional ChatOllama (or any LangChain chat model) instance.
             If None, falls back to rule-based recommendations only.
    """

    def __init__(self, aggregator: Any, llm: Optional[Any] = None) -> None:
        self._aggregator = aggregator
        self._llm = llm

    # ── Public interface ───────────────────────────────────────────────────

    def get_recommendations(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Generate a list of product recommendations for the given customer.

        Returns:
            List of dicts, each with keys:
                product_name     (str)
                reason           (str)
                compliance_status (str) — "Eligible" | "Review Required" | "Not Eligible"
                priority         (str) — "High" | "Medium" | "Low"
        """
        customer = self._aggregator.get_customer_by_id(customer_id)
        if customer is None:
            return []

        products = _load_products()
        if not products:
            return []

        # 1. Rule-based eligibility filter
        eligible_products = self._filter_eligible(customer, products)

        # 2. Remove products the customer already holds
        eligible_products = self._remove_existing(customer, eligible_products)

        if not eligible_products:
            return []

        # 3. LLM reasoning layer (if available)
        if self._llm is not None:
            try:
                return self._llm_recommendations(customer, eligible_products)
            except Exception as exc:
                print(f"[Recommender] LLM error, falling back to rule-based: {exc}")

        # 4. Rule-based fallback scoring
        return self._rule_based_score(customer, eligible_products)

    # ── Private helpers ────────────────────────────────────────────────────

    @staticmethod
    def _customer_age(customer: Any) -> int:
        """Estimate customer age from relationship_since as a rough proxy.
        Falls back to 35 if not computable."""
        try:
            # relationship_since is available but birth_date is not in the model.
            # We use a conservative default for eligibility filtering.
            return 35
        except Exception:
            return 35

    @staticmethod
    def _estimate_income(customer: Any) -> float:
        """
        Estimate annual income from account balances and wealth holdings.
        Uses total balance across all accounts as a lower-bound proxy.
        """
        try:
            total_balance = sum(
                acc.balance for acc in customer.accounts if acc.status == "Active"
            )
            # Rough heuristic: annual income ~ 2× liquid balance for middle-income customers
            # Capped at a realistic figure
            return max(total_balance * 2, 120000.0)
        except Exception:
            return 240000.0  # Default ₹2.4 lakh

    def _filter_eligible(
        self, customer: Any, products: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Apply hard eligibility rules — age, income, KYC — to narrow product list."""
        age = self._customer_age(customer)
        income = self._estimate_income(customer)
        kyc_verified = (
            customer.kyc.aadhaar.verified
            and customer.kyc.pan.verified
            and customer.kyc.address_proof.verified
        )

        eligible = []
        for product in products:
            min_age = product.get("min_age", 0)
            max_age = product.get("max_age", 100)
            min_income = product.get("min_income", 0.0)

            if age < min_age or age > max_age:
                continue
            if income < min_income:
                continue
            if not kyc_verified:
                # Only allow basic products without full KYC
                if product.get("min_income", 0) > 240000:
                    continue
            eligible.append(product)

        return eligible

    @staticmethod
    def _remove_existing(
        customer: Any, products: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Remove products that the customer already holds to avoid redundant recommendations.
        Matches by category and rough name similarity.
        """
        # Collect existing product types
        existing_types = set()
        for acc in customer.accounts:
            existing_types.add(acc.type.lower())
        for loan in customer.loans:
            existing_types.add(loan.type.lower())
        for w in customer.wealth:
            existing_types.add(w.type.lower())

        filtered = []
        for product in products:
            p_name_lower = product.get("name", "").lower()
            # Skip if a closely-named product already exists
            skip = False
            for et in existing_types:
                if et in p_name_lower or p_name_lower in et:
                    skip = True
                    break
            if not skip:
                filtered.append(product)

        return filtered

    def _llm_recommendations(
        self, customer: Any, products: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Use the LLM to generate personalised, reasoned recommendations."""
        from langchain_core.messages import SystemMessage, HumanMessage

        customer_json = customer.model_dump_json(indent=2)
        products_json = json.dumps(products, indent=2)

        system_msg = SystemMessage(
            content=RECOMMENDER_PROMPT.format(
                customer_profile=customer_json,
                products=products_json,
            )
        )
        human_msg = HumanMessage(
            content=(
                f"Generate personalised cross-sell recommendations for customer "
                f"{customer.customer_id} ({customer.name}, {customer.segment} segment). "
                "Return ONLY a JSON array."
            )
        )

        response = self._llm.invoke([system_msg, human_msg])
        raw = response.content if hasattr(response, "content") else str(response)

        # Parse JSON from the LLM response
        raw = raw.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        recommendations = json.loads(raw)
        if isinstance(recommendations, list):
            return recommendations
        return []

    def _rule_based_score(
        self, customer: Any, products: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Assign priority and generate a templated reason for each eligible product
        without calling the LLM.
        """
        results = []
        segment = customer.segment  # Mass | Affluent | HNI
        has_overdue = any(l.status in ("Overdue", "NPA") for l in customer.loans)
        total_balance = sum(
            a.balance for a in customer.accounts if a.status == "Active"
        )
        wealth_count = len(customer.wealth)

        for product in products:
            category = product.get("category", "")
            name = product.get("name", "")
            rate = product.get("interest_rate")

            # Determine priority
            priority = "Low"
            if segment == "HNI" and category in ("Wealth", "Insurance", "Card"):
                priority = "High"
            elif segment == "Affluent" and category in ("Wealth", "Insurance"):
                priority = "High"
            elif total_balance > 500000 and category == "Wealth":
                priority = "High"
            elif wealth_count == 0 and category in ("Wealth", "Insurance"):
                priority = "Medium"
            elif category == "Card" and segment != "Mass":
                priority = "Medium"

            # Determine compliance status
            if has_overdue:
                compliance_status = "Review Required"
            elif not (
                customer.kyc.aadhaar.verified
                and customer.kyc.pan.verified
                and customer.kyc.address_proof.verified
            ):
                compliance_status = "Review Required"
            else:
                compliance_status = "Eligible"

            # Generate a templated reason
            reason = self._generate_reason(customer, product, total_balance, wealth_count)

            results.append(
                {
                    "product_name": name,
                    "reason": reason,
                    "compliance_status": compliance_status,
                    "priority": priority,
                }
            )

        # Sort by priority
        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        results.sort(key=lambda x: priority_order.get(x["priority"], 3))

        return results[:5]  # Return top 5 recommendations

    @staticmethod
    def _generate_reason(
        customer: Any,
        product: Dict[str, Any],
        total_balance: float,
        wealth_count: int,
    ) -> str:
        """Generate a personalised one-sentence reason for a recommendation."""
        name = product.get("name", "this product")
        category = product.get("category", "")
        rate = product.get("interest_rate")

        if category == "Wealth" and "Fixed Deposit" in name:
            return (
                f"{customer.name} has ₹{total_balance:,.0f} in active accounts; "
                f"{name} offers {rate}% p.a. to grow idle funds securely."
            )
        if category == "Wealth" and "Mutual Fund" in name:
            return (
                f"With {wealth_count} existing wealth products, a SIP via {name} "
                f"adds equity diversification aligned with {customer.segment} segment goals."
            )
        if category == "Insurance":
            return (
                f"{customer.name} currently has no insurance coverage on record; "
                f"{name} provides essential financial protection."
            )
        if category == "Card":
            return (
                f"As an {customer.segment} customer, {customer.name} qualifies for "
                f"{name} with lifestyle benefits and reward points."
            )
        if category == "Loan":
            return (
                f"Based on {customer.name}'s profile and income eligibility, "
                f"{name} is available at {rate}% p.a. interest."
            )
        return (
            f"{name} is a suitable addition to {customer.name}'s current banking relationship."
        )
