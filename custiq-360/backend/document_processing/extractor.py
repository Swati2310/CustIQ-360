"""
DocumentExtractor — main extraction pipeline for CustIQ 360° Phase 4.

Pipeline:
  1. Detect file type (.jpg / .jpeg / .png  →  image | .pdf  →  convert first page to PNG)
  2. Try LLaVA (VisionExtractor) for structured JSON extraction.
  3. If LLaVA is unavailable or fails, fall back to pytesseract OCR.
  4. Parse OCR output with regex into the expected schema.
  5. Return a unified result dict.
"""
from __future__ import annotations

import io
import logging
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from document_processing.vision import VisionExtractor

logger = logging.getLogger(__name__)

# Supported extensions grouped by media class
_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
_PDF_EXTENSIONS = {".pdf"}
_ALL_SUPPORTED = _IMAGE_EXTENSIONS | _PDF_EXTENSIONS


class DocumentExtractor:
    """
    High-level extraction pipeline.  Instantiate once and call :meth:`extract`
    for each document.
    """

    def __init__(
        self,
        vision_model: str = "gemini-2.5-flash",
        api_key: str = "",
    ) -> None:
        self._vision = VisionExtractor(model=vision_model, api_key=api_key)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract(self, file_path: str, doc_type: str = "id_proof") -> Dict[str, Any]:
        """
        Extract structured data from *file_path*.

        Returns::

            {
                "success":        bool,
                "doc_type":       str,
                "extracted_data": dict,
                "method":         "llava" | "ocr" | "error",
                "raw_text":       str,   # OCR text when method == "ocr", else ""
            }
        """
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix not in _ALL_SUPPORTED:
            return self._error_result(
                doc_type,
                f"Unsupported file type '{suffix}'. Supported: {', '.join(sorted(_ALL_SUPPORTED))}",
            )

        if not path.exists():
            return self._error_result(doc_type, f"File not found: {file_path}")

        # --- Convert PDF to image (first page) if needed -----------------
        image_path: str = file_path
        _tmp_png: Optional[str] = None

        if suffix in _PDF_EXTENSIONS:
            try:
                image_path, _tmp_png = self._pdf_first_page_to_png(file_path)
            except Exception as exc:
                logger.warning("PDF conversion failed, attempting OCR directly: %s", exc)
                # Fall back to raw OCR on the PDF (tesseract can handle PDFs too)
                raw_text = self._ocr_pdf_fallback(file_path)
                extracted = self.parse_ocr_text(raw_text, doc_type)
                return {
                    "success": bool(extracted),
                    "doc_type": doc_type,
                    "extracted_data": extracted,
                    "method": "ocr",
                    "raw_text": raw_text,
                }

        try:
            # --- Attempt LLaVA extraction ---------------------------------
            vision_result = self._vision.extract_from_image(image_path, doc_type)

            if "error" not in vision_result:
                # Success via LLaVA
                return {
                    "success": True,
                    "doc_type": doc_type,
                    "extracted_data": vision_result,
                    "method": "llava",
                    "raw_text": "",
                }

            # LLaVA returned an error dict — check whether model is available
            llava_available: bool = vision_result.get("available", True)
            llava_error: str = vision_result.get("error", "Unknown LLaVA error")
            logger.warning("LLaVA extraction failed (%s). Falling back to OCR.", llava_error)

            # --- OCR fallback --------------------------------------------
            raw_text = self.ocr_fallback(image_path)
            if raw_text.strip():
                extracted = self.parse_ocr_text(raw_text, doc_type)
                return {
                    "success": bool(extracted),
                    "doc_type": doc_type,
                    "extracted_data": extracted,
                    "method": "ocr",
                    "raw_text": raw_text,
                    # Surface the original LLaVA error so the caller knows what happened
                    "_llava_error": llava_error,
                    "_llava_available": llava_available,
                }

            # Both pipelines failed — return an error
            return self._error_result(
                doc_type,
                f"LLaVA unavailable ({llava_error}) and OCR returned no text.",
                llava_hint=llava_error,
            )

        finally:
            # Clean up the temporary PNG we created from a PDF (if any)
            if _tmp_png and os.path.exists(_tmp_png):
                try:
                    os.remove(_tmp_png)
                except OSError:
                    pass

    # ------------------------------------------------------------------
    # OCR helpers
    # ------------------------------------------------------------------

    def ocr_fallback(self, image_path: str) -> str:
        """
        Run pytesseract OCR on *image_path* and return the extracted text.
        Returns an empty string if pytesseract is not installed or fails.
        """
        try:
            import pytesseract
            from PIL import Image
        except ImportError as exc:
            logger.warning("pytesseract / Pillow not available: %s", exc)
            return ""

        try:
            img = Image.open(image_path)
            # Improve accuracy: convert to greyscale
            if img.mode not in ("L", "RGB"):
                img = img.convert("RGB")
            text: str = pytesseract.image_to_string(img, lang="eng")
            return text
        except Exception as exc:
            logger.warning("OCR failed on %s: %s", image_path, exc)
            return ""

    def parse_ocr_text(self, raw_text: str, doc_type: str) -> Dict[str, str]:
        """
        Parse OCR plain text into a structured dict using regex heuristics.
        Returns a dict conforming to the expected schema for *doc_type*.
        Fields that cannot be found are returned as empty strings.
        """
        if doc_type in ("id_proof", "pan_card", "address_proof"):
            return self._parse_id_proof(raw_text)
        if doc_type == "salary_slip":
            return self._parse_salary_slip(raw_text)
        if doc_type == "property_doc":
            return self._parse_property_doc(raw_text)
        # Unknown doc_type — return raw_text under a generic key
        return {"raw": raw_text}

    # ------------------------------------------------------------------
    # PDF → image conversion
    # ------------------------------------------------------------------

    def _pdf_first_page_to_png(self, pdf_path: str) -> tuple[str, str]:
        """
        Convert the first page of *pdf_path* to a temporary PNG file.

        Returns:
            (png_path, tmp_path) — both point to the same temp file.

        Raises:
            RuntimeError if no PDF rendering library is available.
        """
        # Try pypdf + Pillow path (via rendering).  pypdf alone cannot render
        # to pixels, so we try pdf2image (which uses poppler) first, then fall
        # back to pypdf for text-only extraction.
        try:
            from pdf2image import convert_from_path  # type: ignore

            pages = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=200)
            if not pages:
                raise RuntimeError("pdf2image returned no pages.")
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False, prefix="custiq_pdf_")
            pages[0].save(tmp.name, format="PNG")
            return tmp.name, tmp.name
        except ImportError:
            pass  # pdf2image not available — try Pillow's PDF support

        try:
            from PIL import Image

            img = Image.open(pdf_path)
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False, prefix="custiq_pdf_")
            img.save(tmp.name, format="PNG")
            return tmp.name, tmp.name
        except Exception as exc:
            raise RuntimeError(
                f"Cannot convert PDF to image. Install pdf2image + poppler or Pillow with PDF support. ({exc})"
            ) from exc

    def _ocr_pdf_fallback(self, pdf_path: str) -> str:
        """
        Extract text directly from a PDF using pypdf (text-based PDFs only).
        Falls back to empty string if pypdf is unavailable.
        """
        try:
            from pypdf import PdfReader  # type: ignore
        except ImportError:
            try:
                from PyPDF2 import PdfReader  # type: ignore[no-redef]
            except ImportError:
                logger.warning("Neither pypdf nor PyPDF2 available; cannot extract PDF text.")
                return ""

        try:
            reader = PdfReader(pdf_path)
            texts = []
            for page in reader.pages:
                texts.append(page.extract_text() or "")
            return "\n".join(texts)
        except Exception as exc:
            logger.warning("PDF text extraction failed: %s", exc)
            return ""

    # ------------------------------------------------------------------
    # Per-doc-type OCR parsers
    # ------------------------------------------------------------------

    def _parse_id_proof(self, text: str) -> Dict[str, str]:
        result: Dict[str, str] = {
            "name": "",
            "dob": "",
            "id_number": "",
            "id_type": "",
            "address": "",
            "expiry_date": "",
        }

        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

        # --- id_type detection -------------------------------------------
        text_lower = text.lower()
        if "aadhaar" in text_lower or "aadhar" in text_lower or "uidai" in text_lower:
            result["id_type"] = "Aadhaar"
        elif "permanent account" in text_lower or re.search(r"\bpan\b", text_lower):
            result["id_type"] = "PAN"
        elif "passport" in text_lower:
            result["id_type"] = "Passport"
        elif "driving" in text_lower or "driver" in text_lower or "licence" in text_lower:
            result["id_type"] = "Driver Licence"
        elif "voter" in text_lower or "election" in text_lower:
            result["id_type"] = "Voter ID"

        # --- id_number ---------------------------------------------------
        # Aadhaar: 12 digits often formatted as XXXX XXXX XXXX
        aadhaar_match = re.search(r"\b\d{4}\s\d{4}\s\d{4}\b", text)
        if aadhaar_match:
            result["id_number"] = aadhaar_match.group().replace(" ", "")
        else:
            # PAN: 5 letters + 4 digits + 1 letter
            pan_match = re.search(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", text)
            if pan_match:
                result["id_number"] = pan_match.group()
            else:
                # Generic alphanumeric ID (passport / DL)
                id_match = re.search(r"\b[A-Z]{1,2}[0-9]{7,9}\b", text)
                if id_match:
                    result["id_number"] = id_match.group()

        # --- DOB ---------------------------------------------------------
        dob_match = re.search(
            r"\b(?:DOB|Date of Birth|Birth|Born)[:\s]*([\d]{1,2}[\/\-\.][\d]{1,2}[\/\-\.][\d]{2,4})\b",
            text,
            re.IGNORECASE,
        )
        if dob_match:
            result["dob"] = dob_match.group(1)
        else:
            # Try plain date pattern
            date_match = re.search(r"\b(\d{2}[\/\-\.]\d{2}[\/\-\.]\d{4})\b", text)
            if date_match:
                result["dob"] = date_match.group(1)

        # --- Expiry date -------------------------------------------------
        exp_match = re.search(
            r"\b(?:Expiry|Expires?|Valid(?:\s+until| thru)?|Validity)[:\s]*([\d]{1,2}[\/\-\.][\d]{1,2}[\/\-\.][\d]{2,4})\b",
            text,
            re.IGNORECASE,
        )
        if exp_match:
            result["expiry_date"] = exp_match.group(1)

        # --- Name --------------------------------------------------------
        name_match = re.search(
            r"\b(?:Name|नाम)[:\s]+([A-Z][a-zA-Z\s]{2,40})",
            text,
            re.IGNORECASE,
        )
        if name_match:
            result["name"] = name_match.group(1).strip()
        elif lines:
            # Heuristic: first all-caps line that is at least two words
            for ln in lines:
                if re.match(r"^[A-Z][A-Z\s]{3,}$", ln) and len(ln.split()) >= 2:
                    result["name"] = ln.title()
                    break

        # --- Address -----------------------------------------------------
        addr_match = re.search(
            r"\b(?:Address|Addr|पता)[:\s]+(.+?)(?:\n\n|\Z)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if addr_match:
            result["address"] = " ".join(addr_match.group(1).split())

        return result

    def _parse_salary_slip(self, text: str) -> Dict[str, str]:
        result: Dict[str, str] = {
            "employee_name": "",
            "employer": "",
            "gross_salary": "",
            "net_salary": "",
            "deductions": "",
            "month_year": "",
        }

        # Employee name
        emp_match = re.search(
            r"\b(?:Employee Name|Name of Employee|Emp(?:loyee)?\.?\s*Name)[:\s]+([A-Za-z\s]{3,50})",
            text,
            re.IGNORECASE,
        )
        if emp_match:
            result["employee_name"] = emp_match.group(1).strip()

        # Employer / Company
        comp_match = re.search(
            r"\b(?:Company|Employer|Organisation|Organization|Firm)[:\s]+([A-Za-z0-9\s&\.\-]{3,60})",
            text,
            re.IGNORECASE,
        )
        if comp_match:
            result["employer"] = comp_match.group(1).strip()

        # Gross salary
        gross_match = re.search(
            r"\b(?:Gross(?:\s+Salary)?|Total Earnings?)[:\s₹Rs.]*([0-9,]+(?:\.\d{1,2})?)",
            text,
            re.IGNORECASE,
        )
        if gross_match:
            result["gross_salary"] = gross_match.group(1).replace(",", "")

        # Net salary
        net_match = re.search(
            r"\b(?:Net(?:\s+Salary)?|Take[- ]?Home|Net Pay)[:\s₹Rs.]*([0-9,]+(?:\.\d{1,2})?)",
            text,
            re.IGNORECASE,
        )
        if net_match:
            result["net_salary"] = net_match.group(1).replace(",", "")

        # Total deductions
        ded_match = re.search(
            r"\b(?:Total Deductions?|Deductions?)[:\s₹Rs.]*([0-9,]+(?:\.\d{1,2})?)",
            text,
            re.IGNORECASE,
        )
        if ded_match:
            result["deductions"] = ded_match.group(1).replace(",", "")

        # Month/Year — e.g. "March 2024" or "03/2024"
        month_match = re.search(
            r"\b(?:Salary for|Pay Period|Month)[:\s]*((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|"
            r"Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|"
            r"Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}|\d{2}[\/\-]\d{4})",
            text,
            re.IGNORECASE,
        )
        if month_match:
            result["month_year"] = month_match.group(1).strip()
        else:
            # Plain "March 2024" anywhere in the doc
            plain_match = re.search(
                r"\b((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
                r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
                r"\s+\d{4})\b",
                text,
                re.IGNORECASE,
            )
            if plain_match:
                result["month_year"] = plain_match.group(1).strip()

        return result

    def _parse_property_doc(self, text: str) -> Dict[str, str]:
        result: Dict[str, str] = {
            "owner_name": "",
            "property_address": "",
            "property_value": "",
            "registration_date": "",
        }

        # Owner name
        owner_match = re.search(
            r"\b(?:Owner(?:'s)? Name|Seller|Purchaser|Buyer|Registered in the name of)[:\s]+([A-Za-z\s]{3,60})",
            text,
            re.IGNORECASE,
        )
        if owner_match:
            result["owner_name"] = owner_match.group(1).strip()

        # Property address
        addr_match = re.search(
            r"\b(?:Property Address|Premises|Situated at|Location of Property)[:\s]+(.+?)(?:\n\n|\Z)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if addr_match:
            result["property_address"] = " ".join(addr_match.group(1).split())

        # Property value
        val_match = re.search(
            r"\b(?:Market Value|Consideration|Sale Price|Property Value|Circle Rate)[:\s₹Rs.INR]*([0-9,]+(?:\.\d{1,2})?)",
            text,
            re.IGNORECASE,
        )
        if val_match:
            result["property_value"] = val_match.group(1).replace(",", "")

        # Registration date
        reg_match = re.search(
            r"\b(?:Registration Date|Registered on|Date of Registration)[:\s]*([\d]{1,2}[\/\-\.][\d]{1,2}[\/\-\.][\d]{2,4})\b",
            text,
            re.IGNORECASE,
        )
        if reg_match:
            result["registration_date"] = reg_match.group(1)

        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _error_result(doc_type: str, message: str, llava_hint: str = "") -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "success": False,
            "doc_type": doc_type,
            "extracted_data": {},
            "method": "error",
            "raw_text": "",
            "error": message,
        }
        if llava_hint:
            result["_llava_error"] = llava_hint
        return result
