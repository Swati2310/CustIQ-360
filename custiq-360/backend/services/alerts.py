"""
services/alerts.py
------------------
Proactive Alert Engine for CustIQ 360°.

Scans all customers in the aggregator's in-memory store and surfaces
actionable alerts for relationship managers: expiring KYC, maturing FDs,
dormant accounts, overdue loans, and cross-sell opportunities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, List, Optional


# ---------------------------------------------------------------------------
# Alert data class
# ---------------------------------------------------------------------------


@dataclass
class Alert:
    """Represents a single proactive alert for a customer."""

    alert_type: str          # KYC_EXPIRY | FD_MATURITY | DORMANT_ACCOUNT | OVERDUE_LOAN | CROSS_SELL
    severity: str            # Critical | High | Medium | Low
    customer_id: str
    customer_name: str
    message: str
    recommended_action: str
    metadata: dict = field(default_factory=dict)  # Extra context (dates, amounts, etc.)

    def to_dict(self) -> dict:
        return {
            "alert_type": self.alert_type,
            "severity": self.severity,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "message": self.message,
            "recommended_action": self.recommended_action,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Alert Engine
# ---------------------------------------------------------------------------

# Thresholds (all in days unless noted)
_KYC_EXPIRY_DAYS = 90        # Warn if address proof expires within 90 days
_FD_MATURITY_DAYS = 60       # Warn if FD matures within 60 days
_DORMANT_DAYS = 180          # No transactions within 180 days = dormant risk
_DORMANT_BALANCE_MAX = 1000  # Balance must be < ₹1,000 for dormant alert
_CROSS_SELL_BALANCE_MIN = 500000  # Balance > ₹5,00,000 with no wealth = cross-sell


def _days_until(date_str: Optional[str]) -> Optional[int]:
    """Return days between today and a YYYY-MM-DD date string, or None."""
    if not date_str:
        return None
    try:
        target = datetime.strptime(date_str, "%Y-%m-%d").date()
        return (target - date.today()).days
    except ValueError:
        return None


def _last_transaction_days_ago(account: Any) -> Optional[int]:
    """
    Return how many days ago the most recent transaction occurred.
    Returns None if the account has no transactions.
    """
    if not account.transactions:
        return None
    dates = []
    for txn in account.transactions:
        try:
            d = datetime.strptime(txn.date, "%Y-%m-%d").date()
            dates.append(d)
        except (ValueError, AttributeError):
            continue
    if not dates:
        return None
    most_recent = max(dates)
    return (date.today() - most_recent).days


class AlertEngine:
    """
    Scans all customers in the aggregator and produces Alert objects.

    Args:
        aggregator: CustomerAggregator with an all_customers_full() method.
    """

    def __init__(self, aggregator: Any) -> None:
        self._aggregator = aggregator

    # ── Public interface ───────────────────────────────────────────────────

    def generate_alerts(self) -> List[Alert]:
        """
        Scan all customers and return a list of Alert objects.

        Alert conditions checked (in order):
          1. KYC address proof expiring within 90 days
          2. Fixed Deposit maturing within 60 days
          3. Account balance < ₹1,000 AND no transactions in 180 days (dormant)
          4. Loan with status "Overdue"
          5. No wealth holdings AND balance > ₹5,00,000 (cross-sell opportunity)
        """
        alerts: List[Alert] = []

        try:
            customers = self._aggregator.all_customers_full()
        except Exception as exc:
            print(f"[AlertEngine] Failed to load customers: {exc}")
            return []

        for customer in customers:
            cid = customer.customer_id
            cname = customer.name

            alerts.extend(self._check_kyc_expiry(customer, cid, cname))
            alerts.extend(self._check_fd_maturity(customer, cid, cname))
            alerts.extend(self._check_dormant_accounts(customer, cid, cname))
            alerts.extend(self._check_overdue_loans(customer, cid, cname))
            alerts.extend(self._check_cross_sell(customer, cid, cname))

        # Sort by severity (Critical first)
        severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        alerts.sort(key=lambda a: severity_order.get(a.severity, 4))

        return alerts

    # ── Individual alert checks ────────────────────────────────────────────

    @staticmethod
    def _check_kyc_expiry(customer: Any, cid: str, cname: str) -> List[Alert]:
        """Alert if address proof expires within KYC_EXPIRY_DAYS days."""
        alerts = []
        kyc = customer.kyc
        days = _days_until(kyc.address_proof.expiry)
        if days is None:
            return alerts

        if days < 0:
            alerts.append(
                Alert(
                    alert_type="KYC_EXPIRY",
                    severity="Critical",
                    customer_id=cid,
                    customer_name=cname,
                    message=(
                        f"Address proof ({kyc.address_proof.type}) for {cname} EXPIRED "
                        f"{abs(days)} day(s) ago (expiry: {kyc.address_proof.expiry})."
                    ),
                    recommended_action=(
                        "Immediately contact the customer to submit updated address proof "
                        "documents to avoid account restrictions per RBI KYC norms."
                    ),
                    metadata={
                        "document_type": kyc.address_proof.type,
                        "expiry_date": kyc.address_proof.expiry,
                        "days_expired": abs(days),
                    },
                )
            )
        elif days <= _KYC_EXPIRY_DAYS:
            severity = "High" if days <= 30 else "Medium"
            alerts.append(
                Alert(
                    alert_type="KYC_EXPIRY",
                    severity=severity,
                    customer_id=cid,
                    customer_name=cname,
                    message=(
                        f"Address proof ({kyc.address_proof.type}) for {cname} expires in "
                        f"{days} day(s) on {kyc.address_proof.expiry}."
                    ),
                    recommended_action=(
                        f"Schedule a KYC renewal call with {cname} and collect updated "
                        "address proof before expiry to maintain uninterrupted account access."
                    ),
                    metadata={
                        "document_type": kyc.address_proof.type,
                        "expiry_date": kyc.address_proof.expiry,
                        "days_remaining": days,
                    },
                )
            )
        return alerts

    @staticmethod
    def _check_fd_maturity(customer: Any, cid: str, cname: str) -> List[Alert]:
        """Alert if a Fixed Deposit matures within FD_MATURITY_DAYS days."""
        alerts = []
        for holding in customer.wealth:
            if holding.type != "Fixed Deposit":
                continue
            days = _days_until(holding.maturity_date)
            if days is None:
                continue
            if 0 <= days <= _FD_MATURITY_DAYS:
                severity = "High" if days <= 14 else "Medium"
                amount_str = f"₹{holding.amount:,.0f}"
                alerts.append(
                    Alert(
                        alert_type="FD_MATURITY",
                        severity=severity,
                        customer_id=cid,
                        customer_name=cname,
                        message=(
                            f"Fixed Deposit ({holding.holding_id}) of {amount_str} "
                            f"for {cname} matures in {days} day(s) on {holding.maturity_date}."
                        ),
                        recommended_action=(
                            f"Contact {cname} to discuss FD renewal options, competitive rates, "
                            "or reinvestment into Mutual Funds / Tax Saver FD per their goals."
                        ),
                        metadata={
                            "holding_id": holding.holding_id,
                            "amount": holding.amount,
                            "maturity_date": holding.maturity_date,
                            "days_remaining": days,
                        },
                    )
                )
            elif days < 0:
                # Already matured — not auto-renewed
                alerts.append(
                    Alert(
                        alert_type="FD_MATURITY",
                        severity="High",
                        customer_id=cid,
                        customer_name=cname,
                        message=(
                            f"Fixed Deposit ({holding.holding_id}) of ₹{holding.amount:,.0f} "
                            f"for {cname} matured {abs(days)} day(s) ago and has not been renewed."
                        ),
                        recommended_action=(
                            f"Immediately follow up with {cname} to renew or reinvest the matured FD "
                            "to avoid funds lying idle at savings rate."
                        ),
                        metadata={
                            "holding_id": holding.holding_id,
                            "amount": holding.amount,
                            "maturity_date": holding.maturity_date,
                            "days_past_maturity": abs(days),
                        },
                    )
                )
        return alerts

    @staticmethod
    def _check_dormant_accounts(customer: Any, cid: str, cname: str) -> List[Alert]:
        """
        Alert if an account has balance < ₹1,000 AND no transactions in 180 days.
        Indicates risk of account becoming dormant under RBI guidelines.
        """
        alerts = []
        for account in customer.accounts:
            if account.status == "Closed":
                continue
            if account.balance >= _DORMANT_BALANCE_MAX:
                continue

            txn_days_ago = _last_transaction_days_ago(account)
            is_inactive = txn_days_ago is None or txn_days_ago >= _DORMANT_DAYS

            if is_inactive:
                inactivity_str = (
                    f"{txn_days_ago} day(s)" if txn_days_ago is not None else "an extended period"
                )
                alerts.append(
                    Alert(
                        alert_type="DORMANT_ACCOUNT",
                        severity="Medium",
                        customer_id=cid,
                        customer_name=cname,
                        message=(
                            f"Account {account.account_id} ({account.type}) for {cname} has "
                            f"balance ₹{account.balance:,.2f} with no activity for {inactivity_str}."
                        ),
                        recommended_action=(
                            f"Contact {cname} to initiate at least one transaction to prevent "
                            "account from being classified as dormant and restricted by the bank."
                        ),
                        metadata={
                            "account_id": account.account_id,
                            "account_type": account.type,
                            "balance": account.balance,
                            "days_inactive": txn_days_ago,
                        },
                    )
                )
        return alerts

    @staticmethod
    def _check_overdue_loans(customer: Any, cid: str, cname: str) -> List[Alert]:
        """Alert for loans with status 'Overdue' or 'NPA'."""
        alerts = []
        for loan in customer.loans:
            if loan.status not in ("Overdue", "NPA"):
                continue
            severity = "Critical" if loan.status == "NPA" else "High"
            alerts.append(
                Alert(
                    alert_type="OVERDUE_LOAN",
                    severity=severity,
                    customer_id=cid,
                    customer_name=cname,
                    message=(
                        f"Loan {loan.loan_id} ({loan.type}) for {cname} is {loan.status}. "
                        f"Outstanding: ₹{loan.outstanding:,.0f} | EMI: ₹{loan.emi:,.0f}/month."
                    ),
                    recommended_action=(
                        f"Urgently contact {cname} to arrange EMI payment and discuss "
                        "a restructuring plan to prevent NPA classification and CIBIL impact."
                        if loan.status == "Overdue"
                        else f"Escalate {cname}'s NPA ({loan.loan_id}) to the collections team "
                        "for recovery proceedings as per RBI IRAC norms."
                    ),
                    metadata={
                        "loan_id": loan.loan_id,
                        "loan_type": loan.type,
                        "outstanding": loan.outstanding,
                        "emi": loan.emi,
                        "status": loan.status,
                    },
                )
            )
        return alerts

    @staticmethod
    def _check_cross_sell(customer: Any, cid: str, cname: str) -> List[Alert]:
        """
        Alert if the customer has no wealth holdings but total account balance > ₹5,00,000.
        Signals a prime cross-sell opportunity for FD / MF / Insurance products.
        """
        alerts = []
        if customer.wealth:
            return alerts  # Already has wealth products

        total_balance = sum(
            a.balance for a in customer.accounts if a.status == "Active"
        )
        if total_balance <= _CROSS_SELL_BALANCE_MIN:
            return alerts

        alerts.append(
            Alert(
                alert_type="CROSS_SELL",
                severity="Low",
                customer_id=cid,
                customer_name=cname,
                message=(
                    f"{cname} holds ₹{total_balance:,.0f} in active account(s) but has "
                    "NO wealth products (FD, MF, Insurance, PPF). "
                    "Significant cross-sell opportunity identified."
                ),
                recommended_action=(
                    f"Schedule a wealth advisory call with {cname} to present FD, SIP, "
                    "and life insurance options suited to their ₹{:,.0f} available balance.".format(
                        total_balance
                    )
                ),
                metadata={
                    "total_balance": total_balance,
                    "wealth_count": 0,
                    "segment": customer.segment,
                },
            )
        )
        return alerts
