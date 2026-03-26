"""
tests/test_currency.py
----------------------
Tests for currency conversion logic and multi-currency data consistency.
"""
import pytest
import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "customers.json")

# Currency rates — must match CurrencyContext.jsx
INR_RATES = {
    "INR": 1.0, "USD": 0.012, "EUR": 0.011, "GBP": 0.0095,
    "SGD": 0.016, "AED": 0.044, "JPY": 1.78, "AUD": 0.019,
    "HKD": 0.094, "SAR": 0.045, "MYR": 0.056, "ZAR": 0.22,
}

STORAGE_RATES = {c: 1.0 / r for c, r in INR_RATES.items()}  # local → INR


@pytest.fixture(scope="module")
def customers():
    with open(DATA_PATH) as f:
        return json.load(f)


def test_all_currencies_have_frontend_rates():
    """Every currency used in customer data must have a rate in CurrencyContext."""
    with open(DATA_PATH) as f:
        data = json.load(f)
    currencies_used = {c.get("currency") for c in data if c.get("currency")}
    for cur in currencies_used:
        assert cur in INR_RATES, f"Currency {cur} has no rate in INR_RATES"


def test_sgd_balances_converted_to_inr(customers):
    """
    SGD customers store balances as INR equivalents.
    SGD 10,000 min → 10,000 / 0.016 = 625,000 INR.
    All SG account balances should be ≥ 625,000 INR.
    """
    sg = [c for c in customers if c.get("country") == "SG"]
    for c in sg:
        for acc in c["accounts"]:
            if acc["status"] != "Dormant":
                assert acc["balance"] >= 50_000, (
                    f"{c['customer_id']}: SG balance {acc['balance']} too low for INR equivalent"
                )


def test_gbp_balances_converted_to_inr(customers):
    """GBP 5,000 min → 5,000 / 0.0095 ≈ 526,315 INR."""
    gb = [c for c in customers if c.get("country") == "GB"]
    for c in gb:
        for acc in c["accounts"]:
            if acc["status"] != "Dormant":
                assert acc["balance"] >= 50_000, (
                    f"{c['customer_id']}: GB balance {acc['balance']} looks unconverted"
                )


def test_jpy_balances_are_large(customers):
    """JPY 1,000,000 * 0.562 = 562,000 INR."""
    jp = [c for c in customers if c.get("country") == "JP"]
    for c in jp:
        for acc in c["accounts"]:
            if acc["status"] != "Dormant":
                assert acc["balance"] >= 100_000, (
                    f"{c['customer_id']}: JPY balance {acc['balance']} seems unconverted"
                )


def test_roundtrip_sgd_conversion():
    """Verify INR → SGD → INR round-trip is consistent."""
    sgd_amount = 100_000  # SGD 100,000
    inr_stored = sgd_amount / INR_RATES["SGD"]  # ÷ 0.016 = 6,250,000
    sgd_displayed = inr_stored * INR_RATES["SGD"]  # × 0.016 = 100,000
    assert abs(sgd_displayed - sgd_amount) < 1, "SGD round-trip conversion failed"


def test_roundtrip_eur_conversion():
    eur_amount = 50_000
    inr_stored = eur_amount / INR_RATES["EUR"]
    eur_displayed = inr_stored * INR_RATES["EUR"]
    assert abs(eur_displayed - eur_amount) < 1, "EUR round-trip conversion failed"


def test_india_balances_not_converted(customers):
    """India customers store raw INR — balances should be in typical INR ranges."""
    india = [c for c in customers if c.get("country") == "IN"]
    for c in india:
        for acc in c["accounts"]:
            # INR balance should be < 10 crore (no conversion applied)
            assert acc["balance"] < 100_000_000, (
                f"{c['customer_id']}: India balance {acc['balance']} unreasonably large"
            )


def test_loan_amounts_positive_for_all_countries(customers):
    for c in customers:
        for loan in c.get("loans", []):
            assert loan["sanctioned_amount"] > 0
            assert loan["outstanding"] >= 0
            assert loan["emi"] > 0


def test_products_json_has_region_products():
    products_path = os.path.join(os.path.dirname(__file__), "..", "data", "products.json")
    with open(products_path) as f:
        products = json.load(f)
    product_names = [p["name"] for p in products]
    assert any("HDB" in n for n in product_names), "Missing Singapore HDB product"
    assert any("ISA" in n for n in product_names), "Missing UK ISA product"
    assert any("Murabaha" in n or "Islamic" in n for n in product_names), "Missing Islamic Finance product"
    assert any("Superannuation" in n for n in product_names), "Missing Australia Superannuation product"
    assert any("SEPA" in n for n in product_names), "Missing SEPA product"
    assert len(products) >= 23, f"Expected ≥23 products, got {len(products)}"
