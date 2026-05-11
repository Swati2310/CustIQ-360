"""
tests/test_api.py
-----------------
Integration tests for all FastAPI endpoints using TestClient.
The `client` fixture uses a context manager so the lifespan (startup/shutdown)
runs, which initialises app.state.aggregator.
"""
import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# ── Health ────────────────────────────────────────────────────────────────────

def test_health_check(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ── Customer list / search ────────────────────────────────────────────────────

def test_list_customers_default(client):
    r = client.get("/api/customers")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 95
    assert data["page"] == 1
    assert len(data["customers"]) == 20


def test_list_customers_pagination(client):
    r = client.get("/api/customers?page=2&limit=10")
    assert r.status_code == 200
    data = r.json()
    assert data["page"] == 2
    assert len(data["customers"]) == 10


def test_list_customers_returns_country_fields(client):
    r = client.get("/api/customers?limit=5")
    assert r.status_code == 200
    for c in r.json()["customers"]:
        assert "country" in c
        assert "currency" in c


def test_search_by_name(client):
    r = client.get("/api/customers?search=Tanaka")
    assert r.status_code == 200
    results = r.json()["customers"]
    assert len(results) >= 1
    assert any("Tanaka" in c["name"] for c in results)


def test_search_by_country_customer_name(client):
    r = client.get("/api/customers?search=Klaus")
    assert r.status_code == 200
    results = r.json()["customers"]
    assert len(results) >= 1
    assert any("Klaus" in c["name"] for c in results)


def test_search_no_results(client):
    r = client.get("/api/customers?search=ZZZNOMATCH999")
    assert r.status_code == 200
    assert r.json()["total"] == 0


# ── Customer 360 profile ──────────────────────────────────────────────────────

def test_get_india_customer(client):
    r = client.get("/api/customers/CUST0001")
    assert r.status_code == 200
    c = r.json()
    assert c["customer_id"] == "CUST0001"
    assert c["country"] == "IN"
    assert c["currency"] == "INR"
    assert "accounts" in c
    assert "loans" in c
    assert "wealth" in c
    assert "kyc" in c


def test_get_singapore_customer(client):
    r = client.get("/api/customers/CUST0016")
    assert r.status_code == 200
    c = r.json()
    assert c["country"] == "SG"
    assert c["currency"] == "SGD"
    assert c["region"] == "APAC"


def test_get_uk_customer(client):
    list_r = client.get("/api/customers?search=Sophie Williams")
    customers = list_r.json()["customers"]
    if customers:
        r = client.get(f"/api/customers/{customers[0]['customer_id']}")
        assert r.status_code == 200
        c = r.json()
        assert c["country"] == "GB"
        assert c["currency"] == "GBP"
        assert c["kyc"]["aadhaar"]["type"] == "National Insurance Number"


def test_get_uae_customer_has_emirates_id(client):
    list_r = client.get("/api/customers?search=Mohammed Al-Rashidi")
    customers = list_r.json()["customers"]
    if customers:
        r = client.get(f"/api/customers/{customers[0]['customer_id']}")
        assert r.status_code == 200
        assert r.json()["kyc"]["aadhaar"]["type"] == "Emirates ID"


def test_get_nonexistent_customer(client):
    r = client.get("/api/customers/CUST9999")
    assert r.status_code == 404


def test_customer_profile_has_multi_country_fields(client):
    c = client.get("/api/customers/CUST0001").json()
    for field in ("country", "country_name", "city", "region", "currency", "age"):
        assert field in c, f"Missing field: {field}"


# ── Sub-resources ─────────────────────────────────────────────────────────────

def test_get_accounts(client):
    r = client.get("/api/customers/CUST0001/accounts")
    assert r.status_code == 200
    accounts = r.json()
    assert isinstance(accounts, list)
    assert len(accounts) >= 1
    assert "balance" in accounts[0]


def test_get_loans(client):
    r = client.get("/api/customers/CUST0001/loans")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_wealth(client):
    r = client.get("/api/customers/CUST0001/wealth")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_kyc(client):
    r = client.get("/api/customers/CUST0001/kyc")
    assert r.status_code == 200
    kyc = r.json()
    for field in ("aadhaar", "pan", "address_proof", "risk_category"):
        assert field in kyc


# ── Alerts ────────────────────────────────────────────────────────────────────

def test_get_alerts(client):
    r = client.get("/api/alerts")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_alerts_have_required_fields(client):
    alerts = client.get("/api/alerts").json()
    for alert in alerts[:5]:
        assert any(k in alert for k in ("alert_type", "severity", "customer_id"))


# ── Simulators ────────────────────────────────────────────────────────────────

def test_emi_simulator(client):
    r = client.post("/api/simulate/emi", json={
        "principal": 1000000, "rate_percent": 10.0, "tenure_months": 120
    })
    assert r.status_code == 200
    data = r.json()
    assert "emi" in data
    assert 13000 < data["emi"] < 14000


def test_fd_simulator(client):
    r = client.post("/api/simulate/fd", json={
        "principal": 500000, "rate_percent": 7.5, "tenure_days": 365
    })
    assert r.status_code == 200
    data = r.json()
    assert "maturity_amount" in data
    assert data["maturity_amount"] > 500000


def test_emi_zero_rate(client):
    r = client.post("/api/simulate/emi", json={
        "principal": 120000, "rate_percent": 0.0, "tenure_months": 12
    })
    assert r.status_code == 200


# ── Recommendations ───────────────────────────────────────────────────────────

def test_get_recommendations(client):
    r = client.get("/api/recommendations/CUST0001")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_recommendations_nonexistent_customer(client):
    r = client.get("/api/recommendations/CUST9999")
    assert r.status_code in (404, 200)
