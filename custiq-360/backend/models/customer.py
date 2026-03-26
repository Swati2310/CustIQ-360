from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Transaction(BaseModel):
    date: str = Field(..., description="ISO date string YYYY-MM-DD")
    description: str
    amount: float = Field(..., description="Transaction amount in INR")
    type: Literal["credit", "debit"]


class Account(BaseModel):
    account_id: str
    type: str
    balance: float = Field(..., description="Current balance in INR")
    branch: str
    status: Literal["Active", "Dormant", "Closed"]
    transactions: List[Transaction] = Field(default_factory=list)


class Loan(BaseModel):
    loan_id: str
    type: str
    sanctioned_amount: float = Field(..., description="Sanctioned amount in INR")
    outstanding: float = Field(..., description="Outstanding principal in INR")
    emi: float = Field(..., description="Monthly EMI in INR")
    rate: float = Field(..., description="Annual interest rate as percentage")
    tenure_months: int
    start_date: str = Field(..., description="ISO date string YYYY-MM-DD")
    status: Literal["Active", "Closed", "NPA", "Overdue"]


class WealthHolding(BaseModel):
    holding_id: str
    type: str
    amount: float = Field(..., description="Invested/current value in INR")
    rate: Optional[float] = Field(None, description="Annual return rate as percentage")
    maturity_date: Optional[str] = Field(None, description="ISO date string YYYY-MM-DD")
    fund_name: Optional[str] = None
    policy_number: Optional[str] = None


class KYCDocument(BaseModel):
    type: str = Field(..., description="Document type e.g. Passport, Voter ID, Driving Licence")
    number: str
    verified: bool
    expiry: Optional[str] = Field(None, description="ISO date string YYYY-MM-DD")


class KYC(BaseModel):
    aadhaar: KYCDocument
    pan: KYCDocument
    address_proof: KYCDocument
    risk_category: Literal["Low", "Medium", "High"]
    last_updated: str = Field(..., description="ISO date string YYYY-MM-DD")


class Customer360(BaseModel):
    model_config = ConfigDict(extra="ignore")

    customer_id: str
    name: str
    phone: str = Field(..., description="Phone number with country prefix e.g. +91XXXXXXXXXX")
    email: EmailStr
    segment: Literal["Mass", "Affluent", "HNI"]
    relationship_since: str = Field(..., description="ISO date string YYYY-MM-DD")
    accounts: List[Account] = Field(default_factory=list)
    loans: List[Loan] = Field(default_factory=list)
    wealth: List[WealthHolding] = Field(default_factory=list)
    kyc: KYC
    photo_url: Optional[str] = None
    # Multi-country fields
    country: Optional[str] = "IN"
    country_name: Optional[str] = "India"
    city: Optional[str] = None
    region: Optional[str] = None
    currency: Optional[str] = "INR"
    occupation: Optional[str] = None
    annual_income: Optional[float] = None
    age: Optional[int] = None
