"""
api/alert_routes.py
-------------------
Proactive Alert endpoints for CustIQ 360°.

Exposes the AlertEngine via REST so that the front-end dashboard and
relationship managers can query active alerts without waiting for the
nightly batch job.

Routes (prefix /api, tag "alerts"):
  GET /alerts                         — all active alerts (sorted by severity)
  GET /alerts/{alert_id}              — a single alert by its generated ID
  GET /alerts/customer/{customer_id}  — all alerts for a specific customer
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request

from services.alerts import Alert, AlertEngine

router = APIRouter(prefix="/api", tags=["alerts"])


# ---------------------------------------------------------------------------
# Dependency — obtain AlertEngine wired to the app-state aggregator
# ---------------------------------------------------------------------------


def _get_alert_engine(request: Request) -> AlertEngine:
    """
    FastAPI dependency that builds an AlertEngine from the shared
    CustomerAggregator stored on app.state during startup lifespan.
    """
    aggregator = getattr(request.app.state, "aggregator", None)
    if aggregator is None:
        raise HTTPException(
            status_code=503,
            detail="Customer data store is not initialised yet. Try again shortly.",
        )
    return AlertEngine(aggregator)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _enrich_alert(alert: Alert, index: int) -> Dict[str, Any]:
    """
    Convert an Alert dataclass to a JSON-serialisable dict and attach a
    deterministic alert_id composed from the customer_id + type + index.
    """
    data = alert.to_dict()
    data["alert_id"] = f"{alert.customer_id}-{alert.alert_type}-{index:04d}"
    return data


def _generate_enriched_alerts(engine: AlertEngine) -> List[Dict[str, Any]]:
    """Run the engine and return all alerts with injected alert_ids."""
    raw = engine.generate_alerts()
    return [_enrich_alert(alert, idx) for idx, alert in enumerate(raw)]


# ---------------------------------------------------------------------------
# GET /alerts
# ---------------------------------------------------------------------------


@router.get(
    "/alerts",
    summary="Retrieve all active alerts",
    description=(
        "Runs the AlertEngine against all customers in the in-memory store and "
        "returns every active alert sorted by severity (Critical → High → Medium → Low). "
        "Results are regenerated on each request; no caching is applied."
    ),
    response_model=List[Dict[str, Any]],
)
async def get_all_alerts(
    engine: AlertEngine = Depends(_get_alert_engine),
) -> List[Dict[str, Any]]:
    return _generate_enriched_alerts(engine)


# ---------------------------------------------------------------------------
# GET /alerts/customer/{customer_id}
# ---------------------------------------------------------------------------

# NOTE: This route MUST be declared before /alerts/{alert_id} so that FastAPI
# does not mistakenly match the literal path segment "customer" as an alert_id.


@router.get(
    "/alerts/customer/{customer_id}",
    summary="Retrieve alerts for a specific customer",
    description=(
        "Filters the full alert list to return only those belonging to the "
        "given customer_id. Returns an empty list (not 404) if the customer "
        "exists but has no active alerts."
    ),
    response_model=List[Dict[str, Any]],
)
async def get_alerts_for_customer(
    customer_id: str,
    engine: AlertEngine = Depends(_get_alert_engine),
) -> List[Dict[str, Any]]:
    all_alerts = _generate_enriched_alerts(engine)
    customer_alerts = [a for a in all_alerts if a["customer_id"] == customer_id]

    if not customer_alerts:
        # Verify the customer actually exists; if not, return 404
        aggregator = engine._aggregator
        try:
            customer = aggregator.get_customer(customer_id)
        except Exception:
            customer = None

        if customer is None:
            raise HTTPException(
                status_code=404,
                detail=f"Customer '{customer_id}' not found.",
            )

    return customer_alerts


# ---------------------------------------------------------------------------
# GET /alerts/{alert_id}
# ---------------------------------------------------------------------------


@router.get(
    "/alerts/{alert_id}",
    summary="Retrieve a specific alert by ID",
    description=(
        "Returns a single alert matching the given alert_id. "
        "Alert IDs follow the pattern: {customer_id}-{ALERT_TYPE}-{index}. "
        "Returns 404 if no alert with that ID exists in the current run."
    ),
    response_model=Dict[str, Any],
)
async def get_alert_by_id(
    alert_id: str,
    engine: AlertEngine = Depends(_get_alert_engine),
) -> Dict[str, Any]:
    all_alerts = _generate_enriched_alerts(engine)
    for alert in all_alerts:
        if alert["alert_id"] == alert_id:
            return alert

    raise HTTPException(
        status_code=404,
        detail=f"Alert with ID '{alert_id}' not found.",
    )
