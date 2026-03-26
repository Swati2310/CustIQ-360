"""
FastAPI router — Document Processing endpoints (Phase 4).

Prefix: /api
Routes:
  POST /documents/extract         — upload a document and extract structured data
  GET  /documents/supported-types — list supported doc types and their output fields
"""
from __future__ import annotations

import logging
import os
import shutil
import uuid
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from config import settings
from document_processing.extractor import DocumentExtractor, _ALL_SUPPORTED

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

UPLOAD_DIR = Path("/tmp/custiq_uploads")
MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB

SUPPORTED_TYPES: Dict[str, Dict[str, Any]] = {
    "id_proof": {
        "description": "Primary ID document (Aadhaar, Passport, Emirates ID, NRIC, etc.)",
        "extracted_fields": ["name", "dob", "id_number", "id_type", "address", "expiry_date"],
    },
    "pan_card": {
        "description": "Secondary ID document (PAN Card, SingPass ID, Residency Visa, etc.)",
        "extracted_fields": ["name", "dob", "id_number", "id_type", "expiry_date"],
    },
    "address_proof": {
        "description": "Address proof document (Driving Licence, Utility Bill, Lease Agreement, etc.)",
        "extracted_fields": ["name", "id_number", "id_type", "address", "expiry_date"],
    },
    "salary_slip": {
        "description": "Monthly salary slip / pay stub",
        "extracted_fields": [
            "employee_name",
            "employer",
            "gross_salary",
            "net_salary",
            "deductions",
            "month_year",
        ],
    },
    "property_doc": {
        "description": "Property registration / sale deed document",
        "extracted_fields": [
            "owner_name",
            "property_address",
            "property_value",
            "registration_date",
        ],
    },
}

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/api", tags=["documents"])

# One extractor instance shared across requests (stateless internally)
_extractor = DocumentExtractor(
    vision_model=settings.GEMINI_VISION_MODEL,
    api_key=settings.GEMINI_API_KEY,
)


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class ExtractionResponse(BaseModel):
    success: bool
    doc_type: str
    extracted_data: Dict[str, Any]
    method: str  # "llava" | "ocr" | "error"
    confidence: str  # "high" | "medium" | "low" — heuristic based on method


class SupportedTypeDetail(BaseModel):
    description: str
    extracted_fields: List[str]


class SupportedTypesResponse(BaseModel):
    supported_doc_types: Dict[str, SupportedTypeDetail]
    supported_file_formats: List[str]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ensure_upload_dir() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _confidence_from_method(method: str) -> str:
    return {"llava": "high", "ocr": "medium", "error": "low"}.get(method, "low")


def _save_upload(upload: UploadFile) -> Path:
    """
    Stream the uploaded file to a temp path under UPLOAD_DIR.
    Raises HTTPException on oversized or unsupported files.
    """
    _ensure_upload_dir()

    suffix = Path(upload.filename or "").suffix.lower()
    if suffix not in _ALL_SUPPORTED:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported file type '{suffix}'. "
                f"Accepted: {', '.join(sorted(_ALL_SUPPORTED))}"
            ),
        )

    unique_name = f"{uuid.uuid4().hex}{suffix}"
    dest = UPLOAD_DIR / unique_name

    try:
        total = 0
        with dest.open("wb") as fh:
            while True:
                chunk = upload.file.read(64 * 1024)  # 64 KB chunks
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_FILE_BYTES:
                    fh.close()
                    dest.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum allowed size is {MAX_FILE_BYTES // (1024*1024)} MB.",
                    )
                fh.write(chunk)
    except HTTPException:
        raise
    except Exception as exc:
        dest.unlink(missing_ok=True)
        logger.exception("Failed to save uploaded file")
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {exc}") from exc

    return dest


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post(
    "/documents/extract",
    response_model=ExtractionResponse,
    summary="Extract structured data from a document",
    description=(
        "Upload a document image or PDF and receive structured extracted data.\n\n"
        "- Uses **LLaVA 13B** (via Ollama) as the primary extraction engine.\n"
        "- Falls back to **pytesseract OCR** if LLaVA is unavailable.\n"
        "- Max file size: **10 MB**.\n"
        "- Supported formats: `.jpg`, `.jpeg`, `.png`, `.pdf`.\n\n"
        "The `method` field in the response indicates which pipeline was used: "
        "`llava` (high confidence), `ocr` (medium), or `error`."
    ),
    responses={
        413: {"description": "File too large (> 10 MB)"},
        415: {"description": "Unsupported file type"},
        422: {"description": "Validation error"},
    },
)
async def extract_document(
    file: UploadFile = File(..., description="Document file (.jpg, .jpeg, .png, .pdf)"),
    doc_type: str = Form(
        default="id_proof",
        description="Document type: id_proof | salary_slip | property_doc",
    ),
) -> ExtractionResponse:
    if doc_type not in SUPPORTED_TYPES:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Unknown doc_type '{doc_type}'. "
                f"Choose from: {', '.join(SUPPORTED_TYPES.keys())}"
            ),
        )

    temp_path = _save_upload(file)

    try:
        result = _extractor.extract(str(temp_path), doc_type=doc_type)
    except Exception as exc:
        logger.exception("Extraction pipeline raised an unexpected error")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {exc}") from exc
    finally:
        # Always remove the temp file, even if extraction crashed
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass

    method = result.get("method", "error")
    return ExtractionResponse(
        success=result.get("success", False),
        doc_type=result.get("doc_type", doc_type),
        extracted_data=result.get("extracted_data", {}),
        method=method,
        confidence=_confidence_from_method(method),
    )


@router.get(
    "/documents/supported-types",
    response_model=SupportedTypesResponse,
    summary="List supported document types",
    description=(
        "Returns the document types this service can process, along with the "
        "fields extracted for each type and the supported file formats."
    ),
)
async def supported_types() -> SupportedTypesResponse:
    return SupportedTypesResponse(
        supported_doc_types={
            k: SupportedTypeDetail(**v) for k, v in SUPPORTED_TYPES.items()
        },
        supported_file_formats=sorted(_ALL_SUPPORTED),
    )
