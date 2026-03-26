from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field
from datetime import datetime


class Alert(BaseModel):
    alert_id: str
    customer_id: str
    customer_name: str
    type: Literal[
        "KYC_EXPIRY",
        "FD_MATURITY",
        "DORMANT_ACCOUNT",
        "CHURN_RISK",
        "LOAN_OVERDUE",
    ]
    severity: Literal["HIGH", "MEDIUM", "LOW"]
    message: str
    due_date: Optional[str] = Field(None, description="ISO date string YYYY-MM-DD")
    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="ISO datetime string",
    )
