"""Integration tests for authenticated operational dashboard metrics."""

from collections.abc import Callable

from fastapi.testclient import TestClient

from app.models.user import UserRole


def create_incident(
    client: TestClient,
    headers: dict[str, str],
    *,
    title: str,
    service_name: str,
    severity: str,
) -> dict[str, object]:
    """Create one Incident used to calculate dashboard metrics."""

    response = client.post(
        "/api/incidents",
        headers=headers,
        json={
            "title": title,
            "description": f"Operational details for {title}.",
            "service_name": service_name,
            "severity": severity,
        },
    )

    assert response.status_code == 201

    return response.json()


def change_incident_status(
    client: TestClient,
    headers: dict[str, str],
    incident_id: str,
    status: str,
) -> None:
    """Move an Incident into the requested lifecycle status."""

    response = client.patch(
        f"/api/incidents/{incident_id}",
        headers=headers,
        json={"status": status},
    )

    assert response.status_code == 200
    assert response.json()["status"] == status


def empty_dashboard_summary() -> dict[str, object]:
    """Return the stable zero-value dashboard response contract."""

    return {
        "total_incidents": 0,
        "active_incidents": 0,
        "critical_incidents": 0,
        "resolved_incidents": 0,
        "affected_services": 0,
        "status_counts": {
            "open": 0,
            "investigating": 0,
            "resolved": 0,
            "closed": 0,
        },
        "severity_counts": {
            "low": 0,
            "medium": 0,
            "high": 0,
            "critical": 0,
        },
    }


def test_dashboard_summary_requires_authentication(
    client: TestClient,
) -> None:
    """Require a valid session before exposing operational metrics."""

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Not authenticated"
    }


def test_dashboard_summary_returns_stable_zero_counts(
    client: TestClient,
    authenticated_user_factory: Callable[..., dict[str, object]],
) -> None:
    """Return every supported category when no Incidents exist."""

    viewer = authenticated_user_factory(
        role=UserRole.VIEWER,
    )

    response = client.get(
        "/api/dashboard/summary",
        headers=viewer["headers"],
    )

    assert response.status_code == 200
    assert response.json() == empty_dashboard_summary()


def test_dashboard_summary_calculates_operational_metrics(
    client: TestClient,
    authenticated_user_factory: Callable[..., dict[str, object]],
) -> None:
    """Aggregate lifecycle, severity, and active-service metrics."""

    operator = authenticated_user_factory(
        role=UserRole.OPERATOR,
    )
    viewer = authenticated_user_factory(
        role=UserRole.VIEWER,
    )
    operator_headers = operator["headers"]

    open_incident = create_incident(
        client,
        operator_headers,
        title="Orders API outage",
        service_name="orders-api",
        severity="critical",
    )
    investigating_incident = create_incident(
        client,
        operator_headers,
        title="Payment processing delay",
        service_name="payments-api",
        severity="high",
    )
    resolved_incident = create_incident(
        client,
        operator_headers,
        title="Orders cache saturation",
        service_name="orders-api",
        severity="medium",
    )
    closed_incident = create_incident(
        client,
        operator_headers,
        title="Notification delivery lag",
        service_name="notifications",
        severity="low",
    )

    change_incident_status(
        client,
        operator_headers,
        investigating_incident["id"],
        "investigating",
    )
    change_incident_status(
        client,
        operator_headers,
        resolved_incident["id"],
        "resolved",
    )
    change_incident_status(
        client,
        operator_headers,
        closed_incident["id"],
        "closed",
    )

    response = client.get(
        "/api/dashboard/summary",
        headers=viewer["headers"],
    )

    assert response.status_code == 200
    assert response.json() == {
        "total_incidents": 4,
        "active_incidents": 2,
        "critical_incidents": 1,
        "resolved_incidents": 1,
        # Count distinct services belonging to open or investigating records.
        "affected_services": 2,
        "status_counts": {
            "open": 1,
            "investigating": 1,
            "resolved": 1,
            "closed": 1,
        },
        "severity_counts": {
            "low": 1,
            "medium": 1,
            "high": 1,
            "critical": 1,
        },
    }

    # Keep references explicit so the test setup remains easy to inspect.
    assert open_incident["status"] == "open"
