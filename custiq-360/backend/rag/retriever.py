"""
retriever.py — Semantic search over the FAISS vectorstore for CustIQ 360°.

CustomerRetriever wraps a loaded FAISS vectorstore and exposes three search
methods:
  - search()              — top-k text chunks for a free-form query
  - search_with_scores()  — same but including cosine similarity scores
  - get_customer_context()— filtered context for one specific customer
"""
from __future__ import annotations

from typing import List, Tuple

from langchain_community.vectorstores import FAISS


class CustomerRetriever:
    """Performs semantic search over a pre-built FAISS vectorstore.

    Args:
        vectorstore: A FAISS instance that has already been populated / loaded.
    """

    def __init__(self, vectorstore: FAISS) -> None:
        self._vs = vectorstore

    # ------------------------------------------------------------------ #
    # Core search methods                                                   #
    # ------------------------------------------------------------------ #

    def search(self, query: str, k: int = 5) -> List[str]:
        """Return the top-k most semantically similar text chunks.

        Args:
            query: Natural-language search string.
            k: Number of results to return (default 5).

        Returns:
            List of page_content strings, ordered by descending similarity.

        Raises:
            RuntimeError: If the underlying similarity search fails (e.g.
                Ollama unreachable at query time).
        """
        try:
            docs = self._vs.similarity_search(query, k=k)
        except Exception as exc:
            raise RuntimeError(
                f"Semantic search failed. Ensure Ollama is running. "
                f"Original error: {exc}"
            ) from exc
        return [doc.page_content for doc in docs]

    def search_with_scores(
        self, query: str, k: int = 5
    ) -> List[Tuple[str, float]]:
        """Return the top-k chunks together with their similarity scores.

        Scores are L2 distances from FAISS; lower = more similar.  They are
        re-expressed here as positive relevance scores (higher = more relevant)
        by negating the raw distance so callers get an intuitive ordering.

        Args:
            query: Natural-language search string.
            k: Number of results (default 5).

        Returns:
            List of (page_content, score) tuples, ordered by descending score.

        Raises:
            RuntimeError: If search fails.
        """
        try:
            results = self._vs.similarity_search_with_score(query, k=k)
        except Exception as exc:
            raise RuntimeError(
                f"Semantic search with scores failed. Ensure Ollama is running. "
                f"Original error: {exc}"
            ) from exc

        # FAISS returns L2 distance (lower = better). Convert to a relevance
        # score where higher is better: score = 1 / (1 + distance).
        scored: List[Tuple[str, float]] = []
        for doc, distance in results:
            relevance = float(1.0 / (1.0 + distance))
            scored.append((doc.page_content, round(relevance, 6)))

        # Sort by descending relevance (already sorted by FAISS, but be safe)
        scored.sort(key=lambda t: t[1], reverse=True)
        return scored

    # ------------------------------------------------------------------ #
    # Customer-scoped context                                               #
    # ------------------------------------------------------------------ #

    def get_customer_context(
        self, customer_id: str, query: str, k: int = 3
    ) -> str:
        """Return a combined context string relevant to one customer + query.

        Performs a broad semantic search (k * 4 candidates) and then filters
        to chunks whose metadata contains the given customer_id.  If not enough
        customer-specific chunks are found, the search falls back to the top-k
        unfiltered chunks so the caller always gets a useful response.

        Args:
            customer_id: The customer ID to filter on (e.g. "CUST0001").
            query: Natural-language question / topic.
            k: Number of context chunks to include (default 3).

        Returns:
            A single string joining the selected chunks with newline separators.
            Returns an empty string if the vectorstore has no documents.

        Raises:
            RuntimeError: If the underlying search fails.
        """
        # Fetch a generous pool of candidates so filtering has enough to work with
        pool_size = max(k * 4, 20)
        try:
            results = self._vs.similarity_search_with_score(query, k=pool_size)
        except Exception as exc:
            raise RuntimeError(
                f"Customer context retrieval failed. Ensure Ollama is running. "
                f"Original error: {exc}"
            ) from exc

        # Filter to chunks belonging to this customer
        customer_chunks: List[Tuple[str, float]] = []
        for doc, distance in results:
            meta_cid = doc.metadata.get("customer_id", "")
            if meta_cid == customer_id:
                relevance = float(1.0 / (1.0 + distance))
                customer_chunks.append((doc.page_content, relevance))

        customer_chunks.sort(key=lambda t: t[1], reverse=True)
        top_chunks = customer_chunks[:k]

        # Fallback: if no customer-specific chunks found, use unfiltered top-k
        if not top_chunks:
            top_chunks = [
                (doc.page_content, float(1.0 / (1.0 + distance)))
                for doc, distance in results[:k]
            ]

        context_parts = [chunk for chunk, _ in top_chunks]
        return "\n\n".join(context_parts)
