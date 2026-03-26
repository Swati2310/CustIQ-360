"""
api/simulator_routes.py
-----------------------
Financial Simulator endpoints for CustIQ 360°.

Provides three POST endpoints under /api/simulate:
  - /simulate/emi          — EMI calculation with full amortisation schedule
  - /simulate/fd           — Fixed Deposit maturity projection with TDS
  - /simulate/loan-scenario — Side-by-side loan scenario comparison

All EMI calculations use the standard reducing-balance formula:
    EMI = P × r × (1+r)^n / ((1+r)^n - 1)
    where r = annual_rate / 1200  (monthly rate as a decimal)
"""

from __future__ import annotations

from typing import List, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/api", tags=["simulator"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _monthly_rate(annual_rate_percent: float) -> float:
    """Convert annual percentage rate to a monthly decimal rate."""
    return annual_rate_percent / 1200.0


def _calc_emi(principal: float, annual_rate_percent: float, tenure_months: int) -> float:
    """
    Return the monthly EMI using the reducing-balance formula.

    Special case: if rate == 0, EMI = principal / tenure (flat division).
    """
    if annual_rate_percent == 0:
        return round(principal / tenure_months, 2)
    r = _monthly_rate(annual_rate_percent)
    factor = (1 + r) ** tenure_months
    emi = principal * r * factor / (factor - 1)
    return round(emi, 2)


def _build_amortization(
    principal: float,
    annual_rate_percent: float,
    tenure_months: int,
    emi: float,
) -> List[dict]:
    """
    Build a full amortisation schedule and return a trimmed list:
      - Months 1–12 (or all months if tenure <= 12)
      - The final month (if tenure > 12)

    Each row: {month, emi, principal_component, interest_component, outstanding_balance}
    """
    r = _monthly_rate(annual_rate_percent)
    schedule: List[dict] = []
    balance = principal

    for month in range(1, tenure_months + 1):
        interest_component = round(balance * r, 2)
        principal_component = round(emi - interest_component, 2)

        # Guard against floating-point overshoot on the last month
        if principal_component > balance:
            principal_component = round(balance, 2)

        balance = round(balance - principal_component, 2)
        if balance < 0:
            balance = 0.0

        schedule.append(
            {
                "month": month,
                "emi": round(emi, 2),
                "principal_component": principal_component,
                "interest_component": interest_component,
                "outstanding_balance": balance,
            }
        )

    # Return first 12 + last month (or just all rows if tenure <= 12)
    if tenure_months <= 12:
        return schedule

    trimmed = schedule[:12]
    last = schedule[-1]
    if last not in trimmed:
        trimmed.append(last)
    return trimmed


# ---------------------------------------------------------------------------
# /simulate/emi
# ---------------------------------------------------------------------------


class EMIRequest(BaseModel):
    principal: float = Field(..., gt=0, description="Loan principal in INR")
    rate_percent: float = Field(..., ge=0, description="Annual interest rate (e.g. 8.5 for 8.5%)")
    tenure_months: int = Field(..., gt=0, description="Loan tenure in months")

    @field_validator("principal")
    @classmethod
    def principal_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("principal must be greater than 0")
        return v


class AmortizationRow(BaseModel):
    month: int
    emi: float
    principal_component: float
    interest_component: float
    outstanding_balance: float


class EMIResponse(BaseModel):
    principal: float
    rate_percent: float
    tenure_months: int
    emi: float
    total_interest: float
    total_payment: float
    amortization_schedule: List[AmortizationRow]


@router.post(
    "/simulate/emi",
    response_model=EMIResponse,
    summary="Calculate EMI and amortisation schedule",
    description=(
        "Calculates the monthly EMI for a loan using the reducing-balance formula. "
        "Returns EMI, total interest payable, total payment, and the amortisation schedule "
        "(first 12 months + last month)."
    ),
)
async def simulate_emi(body: EMIRequest) -> EMIResponse:
    emi = _calc_emi(body.principal, body.rate_percent, body.tenure_months)
    total_payment = round(emi * body.tenure_months, 2)
    total_interest = round(total_payment - body.principal, 2)
    schedule = _build_amortization(body.principal, body.rate_percent, body.tenure_months, emi)

    return EMIResponse(
        principal=body.principal,
        rate_percent=body.rate_percent,
        tenure_months=body.tenure_months,
        emi=emi,
        total_interest=total_interest,
        total_payment=total_payment,
        amortization_schedule=[AmortizationRow(**row) for row in schedule],
    )


# ---------------------------------------------------------------------------
# /simulate/fd
# ---------------------------------------------------------------------------

_TDS_THRESHOLD = 40_000.0   # INR — TDS applicable if interest > ₹40,000
_TDS_RATE = 0.10             # 10% TDS

_COMPOUNDING_FREQUENCIES: dict[str, int] = {
    "monthly": 12,
    "quarterly": 4,
    "half-yearly": 2,
    "yearly": 1,
}


class FDRequest(BaseModel):
    principal: float = Field(..., gt=0, description="FD principal amount in INR")
    rate_percent: float = Field(..., gt=0, description="Annual interest rate (e.g. 7.0 for 7%)")
    tenure_days: int = Field(..., gt=0, description="FD tenure in days")
    compounding: str = Field(
        default="quarterly",
        description="Compounding frequency: monthly | quarterly | half-yearly | yearly",
    )

    @field_validator("compounding")
    @classmethod
    def validate_compounding(cls, v: str) -> str:
        v = v.lower()
        if v not in _COMPOUNDING_FREQUENCIES:
            raise ValueError(
                f"compounding must be one of: {', '.join(_COMPOUNDING_FREQUENCIES.keys())}"
            )
        return v


class FDResponse(BaseModel):
    principal: float
    rate_percent: float
    tenure_days: int
    compounding: str
    maturity_amount: float
    interest_earned: float
    effective_yield: float
    tds_applicable: bool
    tds_amount: float


@router.post(
    "/simulate/fd",
    response_model=FDResponse,
    summary="Calculate Fixed Deposit maturity amount",
    description=(
        "Projects the maturity amount for a Fixed Deposit using compound interest. "
        "Applies TDS at 10% if interest earned exceeds ₹40,000 (as per Indian IT Act). "
        "Supported compounding frequencies: monthly, quarterly, half-yearly, yearly."
    ),
)
async def simulate_fd(body: FDRequest) -> FDResponse:
    n = _COMPOUNDING_FREQUENCIES[body.compounding]
    r = body.rate_percent / 100.0
    t = body.tenure_days / 365.0  # Convert days to fractional years

    # Compound interest formula: A = P × (1 + r/n)^(n×t)
    maturity_amount = round(body.principal * ((1 + r / n) ** (n * t)), 2)
    interest_earned = round(maturity_amount - body.principal, 2)

    # Effective annual yield: ((A/P)^(1/t) - 1) × 100
    effective_yield = round(((maturity_amount / body.principal) ** (1 / t) - 1) * 100, 4) if t > 0 else 0.0

    # TDS
    tds_applicable = interest_earned > _TDS_THRESHOLD
    tds_amount = round(interest_earned * _TDS_RATE, 2) if tds_applicable else 0.0

    return FDResponse(
        principal=body.principal,
        rate_percent=body.rate_percent,
        tenure_days=body.tenure_days,
        compounding=body.compounding,
        maturity_amount=maturity_amount,
        interest_earned=interest_earned,
        effective_yield=effective_yield,
        tds_applicable=tds_applicable,
        tds_amount=tds_amount,
    )


# ---------------------------------------------------------------------------
# /simulate/loan-scenario
# ---------------------------------------------------------------------------


class LoanScenarioInput(BaseModel):
    principal: float = Field(..., gt=0, description="Loan principal in INR")
    rate_percent: float = Field(..., ge=0, description="Annual interest rate (%)")
    tenure_months: int = Field(..., gt=0, description="Loan tenure in months")


class LoanScenarioRequest(BaseModel):
    scenario_a: LoanScenarioInput
    scenario_b: LoanScenarioInput


class ScenarioResult(BaseModel):
    emi: float
    total_interest: float
    total_payment: float


class LoanComparisonResult(BaseModel):
    emi_difference: float
    interest_savings: float
    better_option: Literal["A", "B"]


class LoanScenarioResponse(BaseModel):
    scenario_a: ScenarioResult
    scenario_b: ScenarioResult
    comparison: LoanComparisonResult


def _calc_scenario(scenario: LoanScenarioInput) -> ScenarioResult:
    emi = _calc_emi(scenario.principal, scenario.rate_percent, scenario.tenure_months)
    total_payment = round(emi * scenario.tenure_months, 2)
    total_interest = round(total_payment - scenario.principal, 2)
    return ScenarioResult(emi=emi, total_interest=total_interest, total_payment=total_payment)


@router.post(
    "/simulate/loan-scenario",
    response_model=LoanScenarioResponse,
    summary="Compare two loan scenarios side-by-side",
    description=(
        "Accepts two loan configurations (principal, rate, tenure) and returns EMI, "
        "total interest, and total payment for each. Also returns a comparison block "
        "identifying the EMI difference, interest savings, and the better option (A or B) "
        "based on total interest payable."
    ),
)
async def simulate_loan_scenario(body: LoanScenarioRequest) -> LoanScenarioResponse:
    result_a = _calc_scenario(body.scenario_a)
    result_b = _calc_scenario(body.scenario_b)

    emi_difference = round(abs(result_a.emi - result_b.emi), 2)
    interest_savings = round(abs(result_a.total_interest - result_b.total_interest), 2)

    # "Better" = lower total interest (cheaper loan overall)
    better_option: Literal["A", "B"] = "A" if result_a.total_interest <= result_b.total_interest else "B"

    return LoanScenarioResponse(
        scenario_a=result_a,
        scenario_b=result_b,
        comparison=LoanComparisonResult(
            emi_difference=emi_difference,
            interest_savings=interest_savings,
            better_option=better_option,
        ),
    )
