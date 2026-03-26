"""
Gemini vision model integration via the Google Generative AI SDK.

VisionExtractor sends a document image to the Gemini model and asks it to
return structured JSON appropriate for the document type being processed.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Prompts keyed by doc_type.  Each prompt instructs Gemini to return ONLY
# a JSON object (no surrounding markdown fences, no prose) so we can
# json.loads() the response reliably.
_ID_PROOF_PROMPT = (
    "You are a document-reading assistant. Examine this identity document image carefully. "
    "Extract the following fields and return ONLY a valid JSON object — no markdown, no extra text:\n"
    '{"name": "", "dob": "", "id_number": "", "id_type": "", "address": "", "expiry_date": ""}\n'
    "Use empty string for any field you cannot find. "
    'For "id_type" write the exact document type shown (e.g. Aadhaar, PAN, Driving Licence, Passport, Emirates ID, NRIC, Residency Visa, etc.).'
)

_PROMPTS: Dict[str, str] = {
    "id_proof": _ID_PROOF_PROMPT,
    "pan_card": _ID_PROOF_PROMPT,
    "address_proof": _ID_PROOF_PROMPT,
    "salary_slip": (
        "You are a document-reading assistant. Examine this salary slip image carefully. "
        "Extract the following fields and return ONLY a valid JSON object — no markdown, no extra text:\n"
        '{"employee_name": "", "employer": "", "gross_salary": "", "net_salary": "", '
        '"deductions": "", "month_year": ""}\n'
        "Use empty string for any field you cannot find. "
        "Express monetary amounts as plain numbers (e.g. 75000) without currency symbols."
    ),
    "property_doc": (
        "You are a document-reading assistant. Examine this property document image carefully. "
        "Extract the following fields and return ONLY a valid JSON object — no markdown, no extra text:\n"
        '{"owner_name": "", "property_address": "", "property_value": "", "registration_date": ""}\n'
        "Use empty string for any field you cannot find. "
        "Express monetary amounts as plain numbers without currency symbols."
    ),
}

_ID_PROOF_SCHEMA = {
    "name": "",
    "dob": "",
    "id_number": "",
    "id_type": "",
    "address": "",
    "expiry_date": "",
}

_DEFAULT_SCHEMAS: Dict[str, Dict[str, str]] = {
    "id_proof": _ID_PROOF_SCHEMA,
    "pan_card": _ID_PROOF_SCHEMA,
    "address_proof": _ID_PROOF_SCHEMA,
    "salary_slip": {
        "employee_name": "",
        "employer": "",
        "gross_salary": "",
        "net_salary": "",
        "deductions": "",
        "month_year": "",
    },
    "property_doc": {
        "owner_name": "",
        "property_address": "",
        "property_value": "",
        "registration_date": "",
    },
}


class VisionExtractor:
    """
    Sends document images to Gemini via the Google Generative AI SDK and
    returns structured extraction results.
    """

    def __init__(self, model: str = "gemini-2.5-flash", api_key: str = "") -> None:
        self.model = model
        self.api_key = api_key

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_from_image(self, image_path: str, doc_type: str = "id_proof") -> Dict[str, Any]:
        """
        Send *image_path* to LLaVA and return a structured dict.

        Returns:
            On success — the extracted fields dict for the given doc_type.
            On failure — {"error": "<message>", "available": False/True, ...}
        """
        if doc_type not in _PROMPTS:
            supported = ", ".join(_PROMPTS.keys())
            return {
                "error": f"Unsupported doc_type '{doc_type}'. Supported: {supported}",
                "available": True,
            }

        try:
            import io
            from google import genai  # deferred import (google-genai package)
            from google.genai import types
            from PIL import Image as PILImage
        except ImportError:
            return {
                "error": (
                    "The 'google-genai' or 'Pillow' package is not installed. "
                    "Run: pip install google-genai pillow"
                ),
                "available": False,
            }

        if not self.api_key:
            return {
                "error": "GEMINI_API_KEY is not set. Add it to your .env file.",
                "available": False,
            }

        try:
            pil_image = PILImage.open(image_path)
            img_io = io.BytesIO()
            pil_image.save(img_io, format="PNG")
            img_bytes = img_io.getvalue()
        except FileNotFoundError:
            return {"error": f"Image file not found: {image_path}", "available": True}
        except Exception as exc:
            return {"error": f"Failed to read image: {exc}", "available": True}

        prompt = _PROMPTS[doc_type]

        try:
            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model=self.model,
                contents=[
                    types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                    prompt,
                ],
            )
            raw_content: str = response.text
        except Exception as exc:
            err_msg = str(exc)
            if "api_key" in err_msg.lower() or "invalid" in err_msg.lower() or "permission" in err_msg.lower():
                return {
                    "error": "Gemini API key is invalid or lacks permissions.",
                    "available": False,
                    "detail": err_msg,
                }
            if "quota" in err_msg.lower() or "limit" in err_msg.lower():
                return {
                    "error": "Gemini API quota exceeded. Please check your usage limits.",
                    "available": False,
                    "detail": err_msg,
                }
            return {
                "error": f"Gemini request failed: {err_msg}",
                "available": False,
                "detail": err_msg,
            }

        return self._parse_llava_response(raw_content, doc_type)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _parse_llava_response(self, raw: str, doc_type: str) -> Dict[str, Any]:
        """
        Try to extract a JSON object from LLaVA's response.

        LLaVA sometimes wraps the JSON in markdown code fences or adds prose
        before/after.  We strip those defensively.
        """
        # 1. Strip markdown code fences if present
        stripped = re.sub(r"```(?:json)?", "", raw, flags=re.IGNORECASE).strip()

        # 2. Find the first '{' … last '}' substring
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start != -1 and end != -1 and end > start:
            json_candidate = stripped[start : end + 1]
            try:
                parsed = json.loads(json_candidate)
                # Merge with the default schema so all expected keys are present
                result = dict(_DEFAULT_SCHEMAS.get(doc_type, {}))
                result.update({k: str(v) if v is not None else "" for k, v in parsed.items()})
                return result
            except json.JSONDecodeError:
                pass

        # 3. Fallback: return schema with empty strings plus the raw text for debugging
        logger.warning("VisionExtractor: could not parse JSON from LLaVA response for doc_type=%s", doc_type)
        result = dict(_DEFAULT_SCHEMAS.get(doc_type, {}))
        result["_raw_response"] = raw
        return result
