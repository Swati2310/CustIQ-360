from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from models.customer import Account, Customer360, KYC, Loan, WealthHolding
from services.aggregator import CustomerAggregator

router = APIRouter(prefix="/api", tags=["customers"])


# ── Dependency: retrieve the shared aggregator from app state ─────────────


def get_aggregator(request: Request) -> CustomerAggregator:
    return request.app.state.aggregator


# ── Response schemas ──────────────────────────────────────────────────────


class CustomerSummary(BaseModel):
    customer_id: str
    name: str
    phone: str
    email: str
    segment: str
    country: Optional[str] = None
    country_name: Optional[str] = None
    city: Optional[str] = None
    currency: Optional[str] = None


class PaginatedCustomers(BaseModel):
    total: int
    page: int
    limit: int
    total_pages: int
    customers: List[CustomerSummary]


# ── Routes ─────────────────────────────────────────────────────────────────


@router.get(
    "/customers",
    response_model=PaginatedCustomers,
    summary="List / search customers",
    description=(
        "Returns a paginated list of all customers. "
        "Use the `search` parameter for a case-insensitive name/phone/email search."
    ),
)
def list_customers(
    search: Optional[str] = Query(None, description="Search by name, phone, or email"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Records per page"),
    aggregator: CustomerAggregator = Depends(get_aggregator),
) -> PaginatedCustomers:
    if search:
        results: List[Dict[str, str]] = aggregator.search_customers(search)
    else:
        results = aggregator.get_all_customers()

    total = len(results)
    total_pages = max(1, math.ceil(total / limit))
    start = (page - 1) * limit
    end = start + limit
    page_results = results[start:end]

    return PaginatedCustomers(
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        customers=[CustomerSummary(**r) for r in page_results],
    )


@router.get(
    "/customers/{customer_id}",
    response_model=Customer360,
    summary="Get full 360° customer profile",
    description="Returns the complete Customer360 profile including accounts, loans, wealth, and KYC.",
)
def get_customer(
    customer_id: str,
    aggregator: CustomerAggregator = Depends(get_aggregator),
) -> Customer360:
    customer = aggregator.get_customer_by_id(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found.")
    return customer


@router.get(
    "/customers/{customer_id}/accounts",
    response_model=List[Account],
    summary="Get accounts for a customer",
    description="Returns all bank accounts (with recent transactions) for the specified customer.",
)
def get_accounts(
    customer_id: str,
    aggregator: CustomerAggregator = Depends(get_aggregator),
) -> List[Account]:
    accounts = aggregator.get_accounts(customer_id)
    if accounts is None:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found.")
    return accounts


@router.get(
    "/customers/{customer_id}/loans",
    response_model=List[Loan],
    summary="Get loans for a customer",
    description="Returns all loan records for the specified customer.",
)
def get_loans(
    customer_id: str,
    aggregator: CustomerAggregator = Depends(get_aggregator),
) -> List[Loan]:
    loans = aggregator.get_loans(customer_id)
    if loans is None:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found.")
    return loans


@router.get(
    "/customers/{customer_id}/wealth",
    response_model=List[WealthHolding],
    summary="Get wealth holdings for a customer",
    description="Returns all wealth holdings (FDs, MFs, Insurance, PPF) for the specified customer.",
)
def get_wealth(
    customer_id: str,
    aggregator: CustomerAggregator = Depends(get_aggregator),
) -> List[WealthHolding]:
    wealth = aggregator.get_wealth(customer_id)
    if wealth is None:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found.")
    return wealth


@router.get(
    "/customers/{customer_id}/kyc",
    response_model=KYC,
    summary="Get KYC details for a customer",
    description="Returns Aadhaar, PAN, address proof, and risk category for the specified customer.",
)
def get_kyc(
    customer_id: str,
    aggregator: CustomerAggregator = Depends(get_aggregator),
) -> KYC:
    kyc = aggregator.get_kyc(customer_id)
    if kyc is None:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found.")
    return kyc


# ── Document extraction apply ──────────────────────────────────────────────


class ApplyExtractionRequest(BaseModel):
    doc_type: str
    extracted_data: Dict[str, Any]


class ApplyExtractionResponse(BaseModel):
    customer_id: str
    doc_type: str
    updated_fields: Dict[str, Any]
    message: str


@router.patch(
    "/customers/{customer_id}/apply-extraction",
    response_model=ApplyExtractionResponse,
    summary="Apply extracted document data to a customer profile",
    description=(
        "Maps structured fields from a document extraction result onto the "
        "customer's KYC, income, or wealth data, then persists the change."
    ),
)
def apply_extraction(
    customer_id: str,
    body: ApplyExtractionRequest,
    aggregator: CustomerAggregator = Depends(get_aggregator),
) -> ApplyExtractionResponse:
    try:
        updated = aggregator.apply_document_extraction(
            customer_id=customer_id,
            doc_type=body.doc_type,
            extracted_data=body.extracted_data,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to apply extraction: {exc}")

    field_count = len(updated)
    msg = (
        f"Successfully updated {field_count} field(s) from {body.doc_type.replace('_', ' ').title()}."
        if field_count else "No fields were updated — extracted data may be empty."
    )
    return ApplyExtractionResponse(
        customer_id=customer_id,
        doc_type=body.doc_type,
        updated_fields=updated,
        message=msg,
    )
