"""
indexer.py — Builds and persists the FAISS vector index for CustIQ 360°.

CustomerIndexer converts customer (and product) dicts into meaningful natural-
language text chunks, embeds them with nomic-embed-text via Ollama, and stores
the result as a FAISS vectorstore that can be saved to / loaded from disk.

Text chunk layout per customer (~5 chunks):
  1. Profile       — identity, segment, contact, relationship tenure
  2. Accounts      — account-level balances, types, branches, recent activity
  3. Loans         — each loan's type, outstanding, EMI, rate, status
  4. Wealth        — FDs, mutual funds, insurance, PPF holdings
  5. KYC           — documents, risk category, verification status
"""
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from config import get_settings
from rag.embeddings import get_embeddings

settings = get_settings()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt_inr(amount: float) -> str:
    """Format a float as an INR amount string with commas."""
    try:
        return f"₹{amount:,.2f}"
    except (TypeError, ValueError):
        return str(amount)


def _safe(value: Any, default: str = "N/A") -> str:
    """Return string of value, or default if None / empty."""
    if value is None:
        return default
    s = str(value).strip()
    return s if s else default


# ---------------------------------------------------------------------------
# CustomerIndexer
# ---------------------------------------------------------------------------

_EMBED_BATCH_SIZE = 80   # stay under the 100 req/min free-tier limit
_EMBED_BATCH_DELAY = 62  # seconds to wait between batches
_RATE_LIMIT_RETRY_WAIT = 65  # seconds to wait on a 429 before retrying


def _embed_with_retry(fn, *args, max_retries: int = 3, **kwargs):
    """Call fn(*args, **kwargs), retrying on 429 rate-limit errors."""
    for attempt in range(max_retries):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
                wait = _RATE_LIMIT_RETRY_WAIT * (attempt + 1)
                print(f"[indexer] Rate limit hit (attempt {attempt + 1}). Waiting {wait}s before retry…")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("Embedding failed after maximum retries due to rate limiting.")


def _build_faiss_batched(documents: List[Document], embeddings) -> FAISS:
    """Build a FAISS index in batches to respect Gemini free-tier rate limits (100 req/min)."""
    first_batch = documents[:_EMBED_BATCH_SIZE]
    vectorstore = _embed_with_retry(FAISS.from_documents, first_batch, embeddings)

    remaining = documents[_EMBED_BATCH_SIZE:]
    while remaining:
        print(f"[indexer] Batch complete. Pausing {_EMBED_BATCH_DELAY}s before next batch…")
        time.sleep(_EMBED_BATCH_DELAY)
        batch = remaining[:_EMBED_BATCH_SIZE]
        _embed_with_retry(vectorstore.add_documents, batch)
        remaining = remaining[_EMBED_BATCH_SIZE:]

    return vectorstore


class CustomerIndexer:
    """Converts customer/product records into text chunks and builds a FAISS index."""

    # ------------------------------------------------------------------ #
    # Customer text chunks                                                  #
    # ------------------------------------------------------------------ #

    def customer_text_chunks(self, customer: Dict[str, Any]) -> List[str]:
        """Convert a customer record dict into ~5 natural-language text chunks.

        Each chunk covers one aspect of the customer's 360° profile so that
        semantic search can retrieve the most relevant passage for a query.

        Args:
            customer: A dict matching the Customer360 schema.

        Returns:
            A list of non-empty text strings ready for embedding.
        """
        chunks: List[str] = []

        cid = _safe(customer.get("customer_id"))
        name = _safe(customer.get("name"))
        segment = _safe(customer.get("segment"))
        phone = _safe(customer.get("phone"))
        email = _safe(customer.get("email"))
        since = _safe(customer.get("relationship_since"))

        # ── 1. Profile chunk ──────────────────────────────────────────────
        profile_chunk = (
            f"Customer {cid} {name} is a {segment} segment customer. "
            f"Phone: {phone}. Email: {email}. "
            f"Banking relationship since {since}. "
            f"Segment classification: {segment} — "
            + (
                "High Net-worth Individual with premium banking privileges."
                if segment == "HNI"
                else "Affluent customer with mid-tier banking products."
                if segment == "Affluent"
                else "Mass-market retail banking customer."
            )
        )
        chunks.append(profile_chunk)

        # ── 2. Accounts chunk ─────────────────────────────────────────────
        accounts: List[Dict] = customer.get("accounts") or []
        if accounts:
            acc_lines = [
                f"Customer {cid} {name} holds {len(accounts)} bank account(s):"
            ]
            total_balance = 0.0
            for acc in accounts:
                acc_id = _safe(acc.get("account_id"))
                acc_type = _safe(acc.get("type"))
                balance = acc.get("balance") or 0.0
                total_balance += balance
                branch = _safe(acc.get("branch"))
                status = _safe(acc.get("status"))
                acc_lines.append(
                    f"  Account {acc_id}: {acc_type} account at {branch} branch, "
                    f"balance {_fmt_inr(balance)}, status {status}."
                )
                txns: List[Dict] = acc.get("transactions") or []
                if txns:
                    recent = txns[:3]
                    txn_strs = [
                        f"{t.get('description', 'Transaction')} of {_fmt_inr(t.get('amount', 0))} "
                        f"({t.get('type', '')}) on {t.get('date', '')}"
                        for t in recent
                    ]
                    acc_lines.append(
                        f"    Recent transactions: {'; '.join(txn_strs)}."
                    )
            acc_lines.append(
                f"  Total balance across all accounts: {_fmt_inr(total_balance)}."
            )
            chunks.append("\n".join(acc_lines))
        else:
            chunks.append(
                f"Customer {cid} {name} has no bank accounts on record."
            )

        # ── 3. Loans chunk ────────────────────────────────────────────────
        loans: List[Dict] = customer.get("loans") or []
        if loans:
            loan_lines = [
                f"Customer {cid} {name} has {len(loans)} active loan(s):"
            ]
            total_outstanding = 0.0
            total_emi = 0.0
            for loan in loans:
                loan_id = _safe(loan.get("loan_id"))
                loan_type = _safe(loan.get("type"))
                sanctioned = loan.get("sanctioned_amount") or 0.0
                outstanding = loan.get("outstanding") or 0.0
                emi = loan.get("emi") or 0.0
                rate = loan.get("rate") or 0.0
                tenure = _safe(loan.get("tenure_months"))
                start = _safe(loan.get("start_date"))
                status = _safe(loan.get("status"))
                total_outstanding += outstanding
                total_emi += emi
                loan_lines.append(
                    f"  Loan {loan_id}: {loan_type}, sanctioned {_fmt_inr(sanctioned)}, "
                    f"outstanding {_fmt_inr(outstanding)}, EMI {_fmt_inr(emi)}/month, "
                    f"interest rate {rate}% per annum, tenure {tenure} months, "
                    f"start date {start}, status {status}."
                )
            loan_lines.append(
                f"  Total loan outstanding: {_fmt_inr(total_outstanding)}. "
                f"Total monthly EMI burden: {_fmt_inr(total_emi)}."
            )
            chunks.append("\n".join(loan_lines))
        else:
            chunks.append(
                f"Customer {cid} {name} has no outstanding loans."
            )

        # ── 4. Wealth / investments chunk ─────────────────────────────────
        wealth: List[Dict] = customer.get("wealth") or []
        if wealth:
            wealth_lines = [
                f"Customer {cid} {name} holds {len(wealth)} wealth/investment product(s):"
            ]
            total_wealth = 0.0
            for w in wealth:
                hid = _safe(w.get("holding_id"))
                wtype = _safe(w.get("type"))
                amount = w.get("amount") or 0.0
                total_wealth += amount
                rate = w.get("rate")
                maturity = _safe(w.get("maturity_date"), "N/A")
                fund = _safe(w.get("fund_name"), "")
                policy = _safe(w.get("policy_number"), "")

                detail_parts = [
                    f"Holding {hid}: {wtype}, value {_fmt_inr(amount)}"
                ]
                if rate is not None:
                    detail_parts.append(f"rate {rate}% p.a.")
                if maturity != "N/A":
                    detail_parts.append(f"maturing on {maturity}")
                if fund:
                    detail_parts.append(f"fund: {fund}")
                if policy:
                    detail_parts.append(f"policy no: {policy}")
                wealth_lines.append("  " + ", ".join(detail_parts) + ".")

            wealth_lines.append(
                f"  Total wealth portfolio value: {_fmt_inr(total_wealth)}."
            )
            chunks.append("\n".join(wealth_lines))
        else:
            chunks.append(
                f"Customer {cid} {name} has no wealth or investment products on record."
            )

        # ── 5. KYC chunk ──────────────────────────────────────────────────
        kyc: Dict = customer.get("kyc") or {}
        if kyc:
            aadhaar = kyc.get("aadhaar") or {}
            pan = kyc.get("pan") or {}
            addr = kyc.get("address_proof") or {}
            risk = _safe(kyc.get("risk_category"))
            last_updated = _safe(kyc.get("last_updated"))

            def doc_str(doc: Dict) -> str:
                dtype = _safe(doc.get("type"))
                number = _safe(doc.get("number"))
                verified = "verified" if doc.get("verified") else "NOT verified"
                expiry = doc.get("expiry")
                expiry_str = f", expiry {expiry}" if expiry else ""
                return f"{dtype} ({number}), {verified}{expiry_str}"

            kyc_chunk = (
                f"Customer {cid} {name} KYC details: "
                f"Aadhaar — {doc_str(aadhaar)}. "
                f"PAN — {doc_str(pan)}. "
                f"Address proof — {doc_str(addr)}. "
                f"Risk category: {risk}. KYC last updated: {last_updated}."
            )
            chunks.append(kyc_chunk)
        else:
            chunks.append(
                f"Customer {cid} {name} has no KYC information on record."
            )

        return chunks

    # ------------------------------------------------------------------ #
    # Product text chunks                                                   #
    # ------------------------------------------------------------------ #

    def product_text_chunks(self, product: Dict[str, Any]) -> List[str]:
        """Convert a product record dict into natural-language text chunks.

        Args:
            product: A dict matching the products.json schema.

        Returns:
            A list of text strings ready for embedding.
        """
        pid = _safe(product.get("product_id"))
        name = _safe(product.get("name"))
        category = _safe(product.get("category"))
        description = _safe(product.get("description"))
        min_age = _safe(product.get("min_age"))
        max_age = _safe(product.get("max_age"))
        min_income = product.get("min_income")
        interest_rate = product.get("interest_rate")
        features: List[str] = product.get("features") or []

        rate_str = (
            f"Interest/return rate: {interest_rate}% per annum. "
            if interest_rate is not None
            else "No fixed interest rate. "
        )
        income_str = (
            f"Minimum annual income required: {_fmt_inr(min_income)}. "
            if min_income is not None
            else ""
        )
        features_str = (
            "Key features: " + "; ".join(features) + "."
            if features
            else ""
        )

        chunk = (
            f"Product {pid} — {name} (Category: {category}). "
            f"{description} "
            f"Eligible age: {min_age}–{max_age} years. "
            f"{income_str}"
            f"{rate_str}"
            f"{features_str}"
        )
        return [chunk]

    # ------------------------------------------------------------------ #
    # Index building                                                         #
    # ------------------------------------------------------------------ #

    def build_index(self, customers: List[Dict[str, Any]]) -> FAISS:
        """Chunk all customers, embed, and build a FAISS vectorstore.

        Args:
            customers: List of customer record dicts.

        Returns:
            A populated FAISS vectorstore.

        Raises:
            ConnectionError: If Ollama is unreachable during embedding.
            RuntimeError: For any other embedding failure.
        """
        documents: List[Document] = []

        for customer in customers:
            cid = _safe(customer.get("customer_id"))
            name = _safe(customer.get("name"))
            for chunk in self.customer_text_chunks(customer):
                documents.append(
                    Document(
                        page_content=chunk,
                        metadata={"customer_id": cid, "name": name, "source": "customer"},
                    )
                )

        if not documents:
            raise ValueError("No customer documents to index.")

        embeddings = get_embeddings()
        try:
            vectorstore = _build_faiss_batched(documents, embeddings)
        except Exception as exc:
            _raise_connection_error(exc)

        return vectorstore

    def build_index_with_products(
        self,
        customers: List[Dict[str, Any]],
        products: List[Dict[str, Any]],
    ) -> FAISS:
        """Build a FAISS index combining customer and product documents.

        Args:
            customers: List of customer record dicts.
            products: List of product record dicts.

        Returns:
            A populated FAISS vectorstore.
        """
        documents: List[Document] = []

        for customer in customers:
            cid = _safe(customer.get("customer_id"))
            name = _safe(customer.get("name"))
            for chunk in self.customer_text_chunks(customer):
                documents.append(
                    Document(
                        page_content=chunk,
                        metadata={"customer_id": cid, "name": name, "source": "customer"},
                    )
                )

        for product in products:
            pid = _safe(product.get("product_id"))
            pname = _safe(product.get("name"))
            for chunk in self.product_text_chunks(product):
                documents.append(
                    Document(
                        page_content=chunk,
                        metadata={
                            "product_id": pid,
                            "name": pname,
                            "source": "product",
                        },
                    )
                )

        if not documents:
            raise ValueError("No documents to index.")

        embeddings = get_embeddings()
        try:
            vectorstore = _build_faiss_batched(documents, embeddings)
        except Exception as exc:
            _raise_connection_error(exc)

        return vectorstore

    # ------------------------------------------------------------------ #
    # Persistence                                                           #
    # ------------------------------------------------------------------ #

    def save_index(self, vectorstore: FAISS, path: str) -> None:
        """Persist a FAISS vectorstore to disk.

        Args:
            vectorstore: The vectorstore to save.
            path: Directory path where the index files will be written.
        """
        os.makedirs(path, exist_ok=True)
        vectorstore.save_local(path)
        print(f"[indexer] FAISS index saved to: {path}")

    def load_index(self, path: str) -> FAISS:
        """Load a FAISS vectorstore from disk.

        Args:
            path: Directory path containing the saved index files.

        Returns:
            The loaded FAISS vectorstore.

        Raises:
            FileNotFoundError: If the index directory does not exist.
            RuntimeError: If loading fails for any other reason.
        """
        if not os.path.isdir(path):
            raise FileNotFoundError(
                f"FAISS index directory not found: {path}. "
                "Call build_and_save() first or hit GET /api/search/reindex."
            )
        embeddings = get_embeddings()
        try:
            vectorstore = FAISS.load_local(
                path,
                embeddings,
                allow_dangerous_deserialization=True,
            )
        except Exception as exc:
            _raise_connection_error(exc)

        print(f"[indexer] FAISS index loaded from: {path}")
        return vectorstore

    def build_and_save(
        self,
        customers: List[Dict[str, Any]],
        path: str,
        products: List[Dict[str, Any]] | None = None,
    ) -> FAISS:
        """Build the FAISS index and persist it to disk in one step.

        Args:
            customers: List of customer record dicts.
            path: Directory path to save the index.
            products: Optional list of product record dicts to include.

        Returns:
            The built and saved FAISS vectorstore.
        """
        if products:
            vectorstore = self.build_index_with_products(customers, products)
        else:
            vectorstore = self.build_index(customers)
        self.save_index(vectorstore, path)
        return vectorstore


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _raise_connection_error(exc: Exception) -> None:
    """Re-raise exc as a RuntimeError with a helpful Gemini-related message."""
    msg = str(exc).lower()
    if any(kw in msg for kw in ("connection", "refused", "connect", "timeout", "unreachable", "api_key", "invalid")):
        raise RuntimeError(
            "Cannot reach Gemini API. "
            "Check that GEMINI_API_KEY is set correctly in your .env file. "
            f"Original error: {exc}"
        ) from exc
    raise RuntimeError(f"Embedding/indexing failed: {exc}") from exc
