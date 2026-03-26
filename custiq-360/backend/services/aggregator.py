from __future__ import annotations

import json
import os
from threading import Lock
from typing import Any, Dict, List, Optional

from models.customer import Account, Customer360, KYC, Loan, WealthHolding

# Path to the data file — resolved relative to this file's location
_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
_CUSTOMERS_JSON = os.path.join(_DATA_DIR, "customers.json")


class CustomerAggregator:
    """
    In-memory data store that loads customer records from customers.json and
    exposes clean query methods used by the API layer.

    Thread-safe: a Lock protects the internal cache so the aggregator can
    safely be used in multi-threaded Uvicorn workers.
    """

    def __init__(self, data_path: str = _CUSTOMERS_JSON) -> None:
        self._data_path = data_path
        self._customers: Dict[str, Customer360] = {}
        self._lock = Lock()

    # ── Lifecycle ──────────────────────────────────────────────────────────

    def load_customers(self) -> None:
        """Read customers.json and populate the in-memory cache."""
        if not os.path.exists(self._data_path):
            raise FileNotFoundError(
                f"customers.json not found at {self._data_path}. "
                "Run backend/data/seed_data.py to generate it first."
            )
        with open(self._data_path, "r", encoding="utf-8") as f:
            raw: List[Dict[str, Any]] = json.load(f)

        customers: Dict[str, Customer360] = {}
        for record in raw:
            try:
                customer = Customer360.model_validate(record)
                customers[customer.customer_id] = customer
            except Exception as exc:
                # Log bad records and continue loading the rest
                print(f"[CustomerAggregator] Skipping bad record: {exc}")

        with self._lock:
            self._customers = customers

        print(f"[CustomerAggregator] Loaded {len(self._customers)} customers.")

    def reload(self) -> None:
        """Hot-reload customer data without restarting the server."""
        self.load_customers()

    # ── Query methods ──────────────────────────────────────────────────────

    def get_all_customers(self) -> List[Dict[str, str]]:
        """
        Return a lightweight list of all customers.
        Each entry contains: customer_id, name, phone, email, segment,
        country, country_name, city, currency.
        """
        with self._lock:
            return [
                {
                    "customer_id": c.customer_id,
                    "name": c.name,
                    "phone": c.phone,
                    "email": c.email,
                    "segment": c.segment,
                    "country": getattr(c, "country", "IN"),
                    "country_name": getattr(c, "country_name", "India"),
                    "city": getattr(c, "city", None),
                    "currency": getattr(c, "currency", "INR"),
                }
                for c in self._customers.values()
            ]

    def get_customer_by_id(self, customer_id: str) -> Optional[Customer360]:
        """Return the full Customer360 object or None if not found."""
        with self._lock:
            return self._customers.get(customer_id)

    def search_customers(self, query: str) -> List[Dict[str, str]]:
        """
        Case-insensitive substring search across name, phone, and email.
        Returns the same lightweight dict as get_all_customers().
        """
        q = query.strip().lower()
        if not q:
            return self.get_all_customers()

        results = []
        with self._lock:
            for c in self._customers.values():
                if (
                    q in c.name.lower()
                    or q in c.phone.lower()
                    or q in c.email.lower()
                ):
                    results.append(
                        {
                            "customer_id": c.customer_id,
                            "name": c.name,
                            "phone": c.phone,
                            "email": c.email,
                            "segment": c.segment,
                            "country": getattr(c, "country", "IN"),
                            "country_name": getattr(c, "country_name", "India"),
                            "city": getattr(c, "city", None),
                            "currency": getattr(c, "currency", "INR"),
                        }
                    )
        return results

    def get_accounts(self, customer_id: str) -> Optional[List[Account]]:
        """Return list of Account objects for a customer or None if not found."""
        customer = self.get_customer_by_id(customer_id)
        if customer is None:
            return None
        return customer.accounts

    def get_loans(self, customer_id: str) -> Optional[List[Loan]]:
        """Return list of Loan objects for a customer or None if not found."""
        customer = self.get_customer_by_id(customer_id)
        if customer is None:
            return None
        return customer.loans

    def get_wealth(self, customer_id: str) -> Optional[List[WealthHolding]]:
        """Return list of WealthHolding objects for a customer or None if not found."""
        customer = self.get_customer_by_id(customer_id)
        if customer is None:
            return None
        return customer.wealth

    def get_kyc(self, customer_id: str) -> Optional[KYC]:
        """Return the KYC object for a customer or None if not found."""
        customer = self.get_customer_by_id(customer_id)
        if customer is None:
            return None
        return customer.kyc

    # ── Document extraction apply ──────────────────────────────────────────

    def apply_document_extraction(
        self,
        customer_id: str,
        doc_type: str,
        extracted_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Apply extracted document fields to the customer record in-memory
        and persist the change to customers.json.

        Returns a dict of {field: new_value} for all fields that were updated.
        Raises KeyError if the customer is not found.
        """
        with self._lock:
            customer = self._customers.get(customer_id)
            if customer is None:
                raise KeyError(f"Customer '{customer_id}' not found.")

            updated: Dict[str, Any] = {}

            if doc_type == "id_proof":
                # Update primary KYC document (aadhaar slot)
                if extracted_data.get("id_type"):
                    customer.kyc.aadhaar.type = extracted_data["id_type"]
                    updated["kyc.aadhaar.type"] = extracted_data["id_type"]
                if extracted_data.get("id_number"):
                    customer.kyc.aadhaar.number = extracted_data["id_number"]
                    updated["kyc.aadhaar.number"] = extracted_data["id_number"]
                if extracted_data.get("expiry_date"):
                    customer.kyc.aadhaar.expiry = extracted_data["expiry_date"]
                    updated["kyc.aadhaar.expiry"] = extracted_data["expiry_date"]
                # Mark as verified since document was uploaded
                customer.kyc.aadhaar.verified = True
                updated["kyc.aadhaar.verified"] = True
                # Update customer name if extracted and currently missing
                if extracted_data.get("name") and not customer.name:
                    customer.name = extracted_data["name"]
                    updated["name"] = extracted_data["name"]

            elif doc_type == "pan_card":
                # Update secondary KYC document (pan slot)
                if extracted_data.get("id_type"):
                    customer.kyc.pan.type = extracted_data["id_type"]
                    updated["kyc.pan.type"] = extracted_data["id_type"]
                if extracted_data.get("id_number"):
                    customer.kyc.pan.number = extracted_data["id_number"]
                    updated["kyc.pan.number"] = extracted_data["id_number"]
                if extracted_data.get("expiry_date"):
                    customer.kyc.pan.expiry = extracted_data["expiry_date"]
                    updated["kyc.pan.expiry"] = extracted_data["expiry_date"]
                customer.kyc.pan.verified = True
                updated["kyc.pan.verified"] = True

            elif doc_type == "address_proof":
                # Update address proof KYC slot
                if extracted_data.get("id_type"):
                    customer.kyc.address_proof.type = extracted_data["id_type"]
                    updated["kyc.address_proof.type"] = extracted_data["id_type"]
                if extracted_data.get("id_number"):
                    customer.kyc.address_proof.number = extracted_data["id_number"]
                    updated["kyc.address_proof.number"] = extracted_data["id_number"]
                if extracted_data.get("expiry_date"):
                    customer.kyc.address_proof.expiry = extracted_data["expiry_date"]
                    updated["kyc.address_proof.expiry"] = extracted_data["expiry_date"]
                customer.kyc.address_proof.verified = True
                updated["kyc.address_proof.verified"] = True
                if extracted_data.get("address") and not customer.city:
                    customer.city = extracted_data["address"]
                    updated["city"] = extracted_data["address"]

            elif doc_type == "salary_slip":
                gross = extracted_data.get("gross_salary", "")
                if gross:
                    try:
                        annual = float(str(gross).replace(",", "")) * 12
                        customer.annual_income = annual
                        updated["annual_income"] = annual
                    except ValueError:
                        pass
                if extracted_data.get("employer") and not customer.occupation:
                    customer.occupation = extracted_data["employer"]
                    updated["occupation"] = extracted_data["employer"]

            elif doc_type == "property_doc":
                prop_value = extracted_data.get("property_value", "")
                if prop_value:
                    try:
                        value = float(str(prop_value).replace(",", ""))
                        from models.customer import WealthHolding
                        holding = WealthHolding(
                            holding_id=f"DOC_{customer_id}_PROP",
                            type="Real Estate / Property",
                            name=extracted_data.get("property_address", "Uploaded Property") or "Uploaded Property",
                            invested_value=value,
                            current_value=value,
                            maturity_date=None,
                        )
                        customer.wealth.append(holding)
                        updated["wealth.added"] = f"Real Estate / Property — {value:,.0f}"
                    except ValueError:
                        pass

            # Persist updated record to customers.json
            self._persist_customer(customer)
            return updated

    def _persist_customer(self, customer: Customer360) -> None:
        """Write the updated customer back to customers.json (in-place update)."""
        try:
            with open(self._data_path, "r", encoding="utf-8") as f:
                all_records: List[Dict[str, Any]] = json.load(f)

            new_record = json.loads(customer.model_dump_json())
            for i, rec in enumerate(all_records):
                if rec.get("customer_id") == customer.customer_id:
                    all_records[i] = new_record
                    break

            with open(self._data_path, "w", encoding="utf-8") as f:
                json.dump(all_records, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            print(f"[CustomerAggregator] Warning: could not persist update: {exc}")

    # ── Statistics (used by alert engine in later phases) ─────────────────

    def count(self) -> int:
        with self._lock:
            return len(self._customers)

    def all_customers_full(self) -> List[Customer360]:
        """Return all Customer360 objects — used by alert generation pipelines."""
        with self._lock:
            return list(self._customers.values())
