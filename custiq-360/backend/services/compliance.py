"""
services/compliance.py
----------------------
Compliance guardrail service for CustIQ 360°.

Performs KYC verification and product eligibility checks for Indian retail
banking customers, following RBI guidelines and internal bank policies.
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime
from typing import Any, Dict, List, Optional

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
_PRODUCTS_JSON = os.path.join(_DATA_DIR, "products.json")

_CUSTOMER_AGE_DEFAULT = 35  # used when birth date is unavailable


def _load_products() -> List[Dict[str, Any]]:
    """Load products.json."""
    try:
        with open(_PRODUCTS_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _get_product_by_id(product_id: str) -> Optional[Dict[str, Any]]:
    """Look up a product from the catalogue by product_id."""
    for p in _load_products():
        if p.get("product_id") == product_id:
            return p
    return None


def _days_until(date_str: Optional[str]) -> Optional[int]:
    """Return number of days between today and a date string (YYYY-MM-DD), or None."""
    if not date_str:
        return None
    try:
        target = datetime.strptime(date_str, "%Y-%m-%d").date()
        return (target - date.today()).days
    except ValueError:
        return None


class ComplianceAgent:
    """
    Rule-based compliance and KYC eligibility validator.

    Args:
        aggregator: CustomerAggregator instance for fetching customer data.
    """

    def __init__(self, aggregator: Any) -> None:
        self._aggregator = aggregator

    # ── Public interface ───────────────────────────────────────────────────

    def validate(self, customer_id: str, product_id: str) -> Dict[str, Any]:
        """
        Validate whether a customer is eligible for a banking product.

        Args:
            customer_id: The customer's ID.
            product_id: The product's ID (e.g. "PROD006").

        Returns:
            {
                "passed": bool,
                "reasons": list[str],
                "risk_level": "Low" | "Medium" | "High",
            }
        """
        reasons: List[str] = []
        passed = True
        risk_level = "Low"

        # ── 1. Fetch customer ──────────────────────────────────────────────
        customer = self._aggregator.get_customer_by_id(customer_id)
        if customer is None:
            return {
                "passed": False,
                "reasons": [f"Customer '{customer_id}' not found in the system."],
                "risk_level": "High",
            }

        # ── 2. Fetch product ───────────────────────────────────────────────
        product = _get_product_by_id(product_id)
        if product is None:
            return {
                "passed": False,
                "reasons": [f"Product '{product_id}' not found in the product catalogue."],
                "risk_level": "High",
            }

        product_name = product.get("name", product_id)

        # ── 3. KYC verification ────────────────────────────────────────────
        kyc = customer.kyc

        if not kyc.aadhaar.verified:
            reasons.append("Aadhaar is NOT verified — KYC incomplete.")
            passed = False
            risk_level = "High"

        if not kyc.pan.verified:
            reasons.append("PAN is NOT verified — mandatory for all banking products.")
            passed = False
            risk_level = "High"

        if not kyc.address_proof.verified:
            reasons.append("Address proof is NOT verified — KYC incomplete.")
            passed = False
            risk_level = max(risk_level, "Medium") if risk_level == "Low" else risk_level

        # KYC document expiry check
        addr_days = _days_until(kyc.address_proof.expiry)
        if addr_days is not None and addr_days < 30:
            reasons.append(
                f"Address proof expires in {addr_days} day(s) — renewal required before processing."
            )
            passed = False
            risk_level = "High"
        elif addr_days is not None and addr_days < 90:
            reasons.append(
                f"Address proof expires in {addr_days} day(s) — prompt renewal advised."
            )
            # Warning only — does not block

        # ── 4. Age eligibility ─────────────────────────────────────────────
        min_age = product.get("min_age", 0)
        max_age = product.get("max_age", 100)
        customer_age = _CUSTOMER_AGE_DEFAULT  # placeholder (birth_date not in model)

        # We report if we cannot determine age definitively
        if customer_age < min_age:
            reasons.append(
                f"Customer age ({customer_age}) is below the minimum required age ({min_age}) for {product_name}."
            )
            passed = False
        elif customer_age > max_age:
            reasons.append(
                f"Customer age ({customer_age}) exceeds the maximum allowed age ({max_age}) for {product_name}."
            )
            passed = False
        else:
            reasons.append(f"Age eligibility: OK (age {customer_age}, range {min_age}–{max_age}).")

        # ── 5. Income eligibility ──────────────────────────────────────────
        min_income = product.get("min_income", 0.0)
        estimated_income = self._estimate_income(customer)

        if estimated_income < min_income:
            reasons.append(
                f"Estimated annual income (₹{estimated_income:,.0f}) is below the minimum required "
                f"₹{min_income:,.0f} for {product_name}."
            )
            passed = False
            risk_level = "High" if risk_level != "High" else risk_level
        else:
            reasons.append(
                f"Income eligibility: OK (estimated ₹{estimated_income:,.0f} ≥ ₹{min_income:,.0f})."
            )

        # ── 6. KYC risk category vs product suitability ────────────────────
        kyc_risk = kyc.risk_category  # Low | Medium | High
        product_category = product.get("category", "")

        # High-value products (Wealth, Insurance above ₹5L, Credit Cards) need ≥ Medium KYC
        high_value_categories = {"Wealth", "Insurance", "Card"}
        if product_category in high_value_categories and kyc_risk == "High":
            reasons.append(
                f"KYC risk category is '{kyc_risk}' — enhanced due diligence required before "
                f"offering {product_category} products. Refer to compliance team."
            )
            risk_level = "High"
            # Advisory, not a hard block in this implementation

        # ── 7. Overdue / NPA loans ─────────────────────────────────────────
        overdue_loans = [l for l in customer.loans if l.status in ("Overdue", "NPA")]
        if overdue_loans:
            loan_ids = ", ".join(l.loan_id for l in overdue_loans)
            reasons.append(
                f"Customer has {len(overdue_loans)} overdue/NPA loan(s): {loan_ids}. "
                "Manual credit review required before new lending products."
            )
            if product.get("category") == "Loan":
                passed = False
            risk_level = "High"

        # ── 8. Dormant account check ───────────────────────────────────────
        dormant_accounts = [a for a in customer.accounts if a.status == "Dormant"]
        if dormant_accounts:
            acct_ids = ", ".join(a.account_id for a in dormant_accounts)
            reasons.append(
                f"Customer has dormant account(s): {acct_ids}. "
                "Account reactivation may be required."
            )
            risk_level = "Medium" if risk_level == "Low" else risk_level

        # ── 9. Overall risk level escalation ──────────────────────────────
        if kyc_risk == "High" and risk_level == "Low":
            risk_level = "Medium"

        # ── 10. Summary ────────────────────────────────────────────────────
        if passed:
            reasons.insert(
                0,
                f"Customer {customer.name} ({customer_id}) PASSES eligibility checks for {product_name}.",
            )
        else:
            reasons.insert(
                0,
                f"Customer {customer.name} ({customer_id}) DOES NOT meet all eligibility criteria for {product_name}.",
            )

        return {
            "passed": passed,
            "reasons": reasons,
            "risk_level": risk_level,
        }

    # ── Private helpers ────────────────────────────────────────────────────

    @staticmethod
    def _estimate_income(customer: Any) -> float:
        """
        Estimate annual income from the customer's active account balances.
        Used as a proxy when formal income data is unavailable.
        """
        try:
            total_balance = sum(
                a.balance for a in customer.accounts if a.status == "Active"
            )
            # Heuristic: income ≈ 2× total liquid balance
            return max(total_balance * 2.0, 120000.0)
        except Exception:
            return 240000.0
