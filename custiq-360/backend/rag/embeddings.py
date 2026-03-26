"""
embeddings.py — GoogleGenerativeAIEmbeddings wrapper for CustIQ 360°.

Provides a cached singleton of GoogleGenerativeAIEmbeddings backed by the
gemini-embedding-001 model. Import get_embeddings() wherever an embeddings
instance is needed; successive calls return the same object without
re-initialising the client.
"""
from __future__ import annotations

import functools

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from config import get_settings

settings = get_settings()


@functools.lru_cache(maxsize=1)
def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    """Return a cached GoogleGenerativeAIEmbeddings instance."""
    return GoogleGenerativeAIEmbeddings(
        model=settings.GEMINI_EMBED_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
    )
