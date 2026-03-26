"""
search_routes.py — Semantic search endpoints for CustIQ 360° (Phase 2).

Router prefix: /api
Endpoints:
  POST /api/search       — semantic search over the FAISS index
  GET  /api/search/reindex — rebuild FAISS index from customers.json + products.json
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from config import get_settings
from rag.indexer import CustomerIndexer
from rag.retriever import CustomerRetriever

settings = get_settings()

router = APIRouter(prefix="/api", tags=["search"])

# ---------------------------------------------------------------------------
# Data directory helpers
# ---------------------------------------------------------------------------

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CUSTOMERS_JSON = os.path.join(_BACKEND_DIR, "data", "customers.json")
_PRODUCTS_JSON = os.path.join(_BACKEND_DIR, "data", "products.json")


def _load_json(path: str) -> List[Dict[str, Any]]:
    """Load a JSON file and return its contents as a list of dicts."""
    if not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data if isinstance(data, list) else []


# ---------------------------------------------------------------------------
# Shared vectorstore state (process-level singleton)
# ---------------------------------------------------------------------------

_vectorstore_cache: Dict[str, Any] = {"vs": None}


def _get_vectorstore():
    """Return the in-memory vectorstore, loading from disk if needed.

    Raises:
        HTTPException 503: If Ollama is unreachable.
        HTTPException 404: If the index has not been built yet.
    """
    if _vectorstore_cache["vs"] is not None:
        return _vectorstore_cache["vs"]

    indexer = CustomerIndexer()
    faiss_path = settings.FAISS_INDEX_PATH

    try:
        vs = indexer.load_index(faiss_path)
        _vectorstore_cache["vs"] = vs
        return vs
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "FAISS index not found. "
                "Call GET /api/search/reindex to build the index first. "
                f"Details: {exc}"
            ),
        )
    except RuntimeError as exc:
        msg = str(exc)
        if "ollama" in msg.lower() or "connect" in msg.lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Ollama is not reachable. "
                    "Please start Ollama (`ollama serve`) and ensure the "
                    "nomic-embed-text model is available "
                    "(`ollama pull nomic-embed-text`). "
                    f"Details: {msg}"
                ),
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load FAISS index: {msg}",
        )


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class SearchRequest(BaseModel):
    """Body schema for POST /api/search."""

    query: str = Field(..., min_length=1, description="Natural-language search query.")
    customer_id: Optional[str] = Field(
        None,
        description="Optional customer ID to narrow results to a specific customer.",
    )
    k: int = Field(5, ge=1, le=50, description="Number of results to return.")


class SearchResult(BaseModel):
    """A single semantic search result."""

    text: str
    score: float


class SearchResponse(BaseModel):
    """Response schema for POST /api/search."""

    results: List[SearchResult]
    query: str
    customer_id: Optional[str] = None
    total_results: int


class ReindexResponse(BaseModel):
    """Response schema for GET /api/search/reindex."""

    status: str
    customers_indexed: int
    products_indexed: int
    chunks_created: int
    index_path: str
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Semantic search over customer/product data",
    description=(
        "Performs a vector similarity search over the FAISS index built from "
        "customer and product records. Optionally filter results to a specific "
        "customer by providing `customer_id`."
    ),
)
async def semantic_search(body: SearchRequest) -> SearchResponse:
    """POST /api/search

    Body:
        query (str): Free-form search question.
        customer_id (str, optional): Restrict results to this customer.
        k (int): Number of top results to return (default 5, max 50).

    Returns:
        SearchResponse with a list of {text, score} result objects.
    """
    vs = _get_vectorstore()
    retriever = CustomerRetriever(vs)

    try:
        if body.customer_id:
            # Customer-scoped retrieval
            context = retriever.get_customer_context(
                customer_id=body.customer_id,
                query=body.query,
                k=body.k,
            )
            # get_customer_context returns a single joined string; split back
            # into individual chunks so we can return scored results.
            raw_chunks = [c.strip() for c in context.split("\n\n") if c.strip()]
            # Re-score them so the response shape is consistent
            scored = retriever.search_with_scores(body.query, k=body.k * 2)
            # Filter to customer-specific chunks that appear in the context
            context_set = set(raw_chunks)
            results = [
                SearchResult(text=text, score=score)
                for text, score in scored
                if text in context_set
            ]
            # Fallback: if filtering produced nothing, use raw chunks with score 0
            if not results:
                results = [
                    SearchResult(text=chunk, score=0.0) for chunk in raw_chunks[: body.k]
                ]
        else:
            # Global semantic search
            scored = retriever.search_with_scores(body.query, k=body.k)
            results = [SearchResult(text=text, score=score) for text, score in scored]

    except RuntimeError as exc:
        msg = str(exc)
        if "ollama" in msg.lower() or "connect" in msg.lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Ollama is not reachable. "
                    "Please start Ollama (`ollama serve`) and ensure the "
                    "nomic-embed-text model is available. "
                    f"Details: {msg}"
                ),
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {msg}",
        )

    return SearchResponse(
        results=results,
        query=body.query,
        customer_id=body.customer_id,
        total_results=len(results),
    )


@router.get(
    "/search/reindex",
    response_model=ReindexResponse,
    summary="Rebuild the FAISS semantic search index",
    description=(
        "Reads customers.json and products.json, converts every record into "
        "natural-language text chunks, embeds them with nomic-embed-text via "
        "Ollama, and saves the resulting FAISS index to disk. "
        "This replaces any existing index."
    ),
)
async def reindex() -> ReindexResponse:
    """GET /api/search/reindex

    Triggers a full rebuild of the FAISS index.  This is a synchronous
    (blocking) operation that may take tens of seconds depending on the
    number of customers and Ollama's throughput.

    Returns:
        ReindexResponse summarising how many records were indexed.
    """
    customers = _load_json(_CUSTOMERS_JSON)
    products = _load_json(_PRODUCTS_JSON)

    if not customers:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"No customers found in {_CUSTOMERS_JSON}. "
                "Ensure the data file exists and is a non-empty JSON array."
            ),
        )

    indexer = CustomerIndexer()

    # Count chunks so we can report them without re-generating
    total_chunks = sum(
        len(indexer.customer_text_chunks(c)) for c in customers
    ) + sum(len(indexer.product_text_chunks(p)) for p in products)

    faiss_path = settings.FAISS_INDEX_PATH

    try:
        vs = indexer.build_and_save(
            customers=customers,
            path=faiss_path,
            products=products if products else None,
        )
    except RuntimeError as exc:
        msg = str(exc)
        if "ollama" in msg.lower() or "connect" in msg.lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Ollama is not reachable. Cannot generate embeddings. "
                    "Please start Ollama (`ollama serve`) and ensure the "
                    "nomic-embed-text model is pulled "
                    "(`ollama pull nomic-embed-text`). "
                    f"Details: {msg}"
                ),
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Indexing failed: {msg}",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    # Invalidate the in-memory cache so the next search loads the fresh index
    _vectorstore_cache["vs"] = vs

    return ReindexResponse(
        status="ok",
        customers_indexed=len(customers),
        products_indexed=len(products),
        chunks_created=total_chunks,
        index_path=os.path.abspath(faiss_path),
        message=(
            f"Successfully indexed {len(customers)} customer(s) and "
            f"{len(products)} product(s) into {total_chunks} text chunks."
        ),
    )
