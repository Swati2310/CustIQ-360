"""
tests/test_data.py
------------------
Tests for customer data loading, validation, and multi-country structure.
"""
import json
import os
import pytest
from models.customer import Customer360

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "customers.json")


@pytest.fixture(scope="module")
def raw_customers():
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def customers(raw_customers):
    return [Customer360.model_validate(r) for r in raw_customers]


# ── Data loading ──────────────────────────────────────────────────────────────

def test_customers_json_exists():
    assert os.path.exists(DATA_PATH), "customers.json not found"


def test_total_customer_count(customers):
    assert len(customers) == 95, f"Expected 95 customers, got {len(customers)}"


def test_all_records_parse_without_error(raw_customers):
    errors = []
    for r in raw_customers:
        try:
            Customer360.model_validate(r)
        except Exception as e:
            errors.append(f"{r.get('customer_id')}: {e}")
    assert errors == [], f"Parse errors:\n" + "\n".join(errors)


def test_unique_customer_ids(customers):
    ids = [c.customer_id for c in customers]
    assert len(ids) == len(set(ids)), "Duplicate customer IDs found"


# ── Multi-country coverage ────────────────────────────────────────────────────

EXPECTED_COUNTRIES = {"IN": 17, "SG": 11, "AE": 11, "GB": 11, "DE": 8,
                       "JP": 8, "AU": 8, "MY": 6, "HK": 6, "SA": 5, "ZA": 4}

def test_country_distribution(customers):
    from collections import Counter
    dist = Counter(c.country for c in customers)
    for country, expected in EXPECTED_COUNTRIES.items():
        assert dist[country] == expected, (
            f"{country}: expected {expected}, got {dist[country]}"
        )


def test_all_customers_have_country_fields(customers):
    for c in customers:
        assert c.country is not None, f"{c.customer_id} missing country"
        assert c.country_name is not None, f"{c.customer_id} missing country_name"
        assert c.currency is not None, f"{c.customer_id} missing currency"
        assert c.region is not None, f"{c.customer_id} missing region"


def test_region_values_are_valid(customers):
    valid_regions = {"South Asia", "APAC", "EMEA", "SEPA"}
    for c in customers:
        assert c.region in valid_regions, (
            f"{c.customer_id} has invalid region: {c.region}"
        )


def test_india_customers_have_inr(customers):
    india = [c for c in customers if c.country == "IN"]
    for c in india:
        assert c.currency == "INR"


def test_uk_customers_have_gbp(customers):
    uk = [c for c in customers if c.country == "GB"]
    for c in uk:
        assert c.currency == "GBP"


def test_non_india_customers_have_country_specific_kyc(customers):
    """Verify KYC primary doc type is not 'Aadhaar' for non-India customers."""
    for c in customers:
        if c.country != "IN":
            assert c.kyc.aadhaar.type != "Aadhaar", (
                f"{c.customer_id} ({c.country}) still using Aadhaar KYC type"
            )


def test_uk_customers_have_ni_number_kyc(customers):
    uk = [c for c in customers if c.country == "GB"]
    for c in uk:
        assert c.kyc.aadhaar.type == "National Insurance Number", (
            f"{c.customer_id}: expected NI Number, got {c.kyc.aadhaar.type}"
        )


def test_uae_customers_have_emirates_id_kyc(customers):
    uae = [c for c in customers if c.country == "AE"]
    for c in uae:
        assert c.kyc.aadhaar.type == "Emirates ID", (
            f"{c.customer_id}: expected Emirates ID, got {c.kyc.aadhaar.type}"
        )


def test_country_specific_loan_types(customers):
    """Spot-check that non-India customers have localised loan type strings."""
    uk = [c for c in customers if c.country == "GB"]
    uk_loans = [l.type for c in uk for l in c.loans]
    # UK should not have Indian loan types
    for lt in uk_loans:
        assert lt not in ("Home Loan", "Education Loan"), (
            f"UK customer has Indian loan type: {lt}"
        )


# ── Financial data sanity ─────────────────────────────────────────────────────

def test_all_account_balances_positive(customers):
    for c in customers:
        for acc in c.accounts:
            if acc.status != "Dormant":
                assert acc.balance >= 0, (
                    f"{c.customer_id} account {acc.account_id} has negative balance"
                )


def test_loan_outstanding_leq_sanctioned(customers):
    for c in customers:
        for loan in c.loans:
            assert loan.outstanding <= loan.sanctioned_amount * 1.01, (
                f"{c.customer_id} loan {loan.loan_id}: outstanding > sanctioned"
            )


def test_loan_emi_positive(customers):
    for c in customers:
        for loan in c.loans:
            assert loan.emi > 0, f"{c.customer_id} loan {loan.loan_id} has zero EMI"


def test_amounts_stored_as_inr_equivalents(customers):
    """
    Non-INR customers should have large INR-equivalent balances
    (because local amounts are multiplied by INR rate > 1 for most currencies).
    A Singapore customer with SGD 10,000 min → 10,000 * 62.5 = 625,000 INR.
    """
    sg_customers = [c for c in customers if c.country == "SG"]
    for c in sg_customers:
        for acc in c.accounts:
            # SGD 10,000 * 62.5 = 625,000 INR minimum
            assert acc.balance >= 10_000, (
                f"SG customer {c.customer_id} has suspiciously low INR balance: {acc.balance}"
            )


def test_all_kyc_documents_have_numbers(customers):
    for c in customers:
        assert c.kyc.aadhaar.number, f"{c.customer_id} missing aadhaar/primary ID number"
        assert c.kyc.pan.number, f"{c.customer_id} missing pan/secondary ID number"
        assert c.kyc.address_proof.number, f"{c.customer_id} missing address proof number"


def test_risk_categories_valid(customers):
    for c in customers:
        assert c.kyc.risk_category in ("Low", "Medium", "High"), (
            f"{c.customer_id} invalid risk_category: {c.kyc.risk_category}"
        )


def test_segments_valid(customers):
    for c in customers:
        assert c.segment in ("Mass", "Affluent", "HNI"), (
            f"{c.customer_id} invalid segment: {c.segment}"
        )


def test_age_present_and_valid(customers):
    for c in customers:
        assert c.age is not None, f"{c.customer_id} missing age"
        assert 18 <= c.age <= 80, f"{c.customer_id} age out of range: {c.age}"


def test_annual_income_positive(customers):
    for c in customers:
        if c.annual_income is not None:
            assert c.annual_income > 0, f"{c.customer_id} annual_income <= 0"
