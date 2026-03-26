from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class Product(BaseModel):
    product_id: str
    name: str
    category: Literal["CASA", "Loan", "Wealth", "Insurance", "Card"]
    min_age: int = Field(..., ge=18, description="Minimum eligible age")
    max_age: int = Field(..., le=100, description="Maximum eligible age")
    min_income: float = Field(..., description="Minimum annual income in INR")
    description: str
    interest_rate: Optional[float] = Field(None, description="Annual interest/return rate as percentage")
    features: List[str] = Field(default_factory=list)
