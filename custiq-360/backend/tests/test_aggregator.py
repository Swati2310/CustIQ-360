"""
tests/test_aggregator.py
------------------------
Tests for CustomerAggregator service logic.
"""
import pytest
from services.aggregator import CustomerAggregator


@pytest.fixture(scope="module")
def aggregator():
    agg = CustomerAggregator()
    agg.load_customers()
    return agg


def test_aggregator_loads_all_customers(aggregator):
    assert aggregator.count() == 95


def test_get_all_customers_returns_summaries(aggregator):
    summaries = aggregator.get_all_customers()
    assert len(summaries) == 95
    for s in summaries:
        assert "customer_id" in s
        assert "name" in s
        assert "phone" in s
        assert "email" in s
        assert "segment" in s
        assert "country" in s
        assert "currency" in s


def test_search_by_name(aggregator):
    results = aggregator.search_customers("Tanaka")
    assert len(results) >= 1
    assert all("Tanaka" in r["name"] for r in results)


def test_search_by_phone_prefix(aggregator):
    results = aggregator.search_customers("+65")
    assert len(results) >= 1  # Singapore customers
    for r in results:
        assert r["country"] == "SG"


def test_search_by_uk_phone(aggregator):
    results = aggregator.search_customers("+44")
    assert len(results) >= 1
    for r in results:
        assert r["country"] == "GB"


def test_search_empty_returns_all(aggregator):
    results = aggregator.search_customers("")
    assert len(results) == 95


def test_search_no_results(aggregator):
    results = aggregator.search_customers("ZZZNOMATCH999")
    assert results == []


def test_get_customer_by_id(aggregator):
    c = aggregator.get_customer_by_id("CUST0001")
    assert c is not None
    assert c.customer_id == "CUST0001"


def test_get_nonexistent_customer(aggregator):
    c = aggregator.get_customer_by_id("CUST9999")
    assert c is None


def test_get_accounts(aggregator):
    accounts = aggregator.get_accounts("CUST0001")
    assert accounts is not None
    assert isinstance(accounts, list)
    assert len(accounts) >= 1


def test_get_loans(aggregator):
    loans = aggregator.get_loans("CUST0001")
    assert loans is not None
    assert isinstance(loans, list)


def test_get_wealth(aggregator):
    wealth = aggregator.get_wealth("CUST0001")
    assert wealth is not None
    assert isinstance(wealth, list)


def test_get_kyc(aggregator):
    kyc = aggregator.get_kyc("CUST0001")
    assert kyc is not None
    assert kyc.risk_category in ("Low", "Medium", "High")


def test_all_full_customers_have_country(aggregator):
    for c in aggregator.all_customers_full():
        assert c.country is not None
        assert c.region is not None


def test_country_distribution(aggregator):
    from collections import Counter
    dist = Counter(c.country for c in aggregator.all_customers_full())
    assert dist["IN"] == 17
    assert dist["SG"] == 11
    assert dist["GB"] == 11
    assert dist["DE"] == 8
    assert dist["JP"] == 8
    assert dist["AU"] == 8


def test_reload_does_not_crash(aggregator):
    aggregator.reload()
    assert aggregator.count() == 95


def test_summary_includes_city(aggregator):
    summaries = aggregator.get_all_customers()
    sg = [s for s in summaries if s.get("country") == "SG"]
    assert len(sg) == 11
    for s in sg:
        assert s.get("city") is not None
