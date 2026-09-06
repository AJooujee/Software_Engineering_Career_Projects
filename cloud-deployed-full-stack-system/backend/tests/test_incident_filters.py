"""Integration tests for authenticated Incident query filtering."""

from collections.abc import Callable

from fastapi.testclient import TestClient

from app.models.user import UserRole


def create_incident(
    client: TestClient,
    headers: dict[str, str],
    *,
    title: str,
    description: str,
    service_name: str,
    severity: str,
) -> dict[str, object]:
    """Create one Incident through the public API for test setup."""

    response = client.post(
        "/api/incidents",
        headers=headers,
        json={
            "title": title,
            "description": description,
            "service_name": service_name,
            "severity": severity,
        },
    )

    assert response.status_code == 201

    return response.json()


def test_incidents_can_be_filtered_by_search_and_service(
    client: TestClient,
    authenticated_user_factory: Callable[..., dict[str, object]],
) -> None:
    """Search readable fields and match service names case-insensitively."""

    operator = authenticated_user_factory(
        role=UserRole.OPERATOR,
    )
    headers = operator["headers"]

    payment_incident = create_incident(
        client,
        headers,
        title="Payment API latency",
        description="Checkout requests are delayed.",
        service_name="payments-api",
        severity="high",
    )
    inventory_incident = create_incident(
        client,
        headers,
        title="Inventory synchronization lag",
        description="Warehouse stock updates are delayed.",
        service_name="inventory-worker",
        severity="medium",
    )
    create_incident(
        client,
        headers,
        title="Email delivery delay",
        description="Notification messages are queued.",
        service_name="notifications",
        severity="low",
    )

    # Search should inspect title, description, and service name without
    # requiring callers to match letter casing.
    search_response = client.get(
        "/api/incidents",
        headers=headers,
        params={"search": "WAREHOUSE"},
    )

    service_response = client.get(
        "/api/incidents",
        headers=headers,
        params={"service_name": "PAYMENTS-API"},
    )

    assert search_response.status_code == 200
    assert [
        incident["id"]
        for incident in search_response.json()
    ] == [inventory_incident["id"]]

    assert service_response.status_code == 200
    assert [
        incident["id"]
        for incident in service_response.json()
    ] == [payment_incident["id"]]


def test_incidents_can_use_combined_enum_filters(
    client: TestClient,
    authenticated_user_factory: Callable[..., dict[str, object]],
) -> None:
    """Combine status and severity filters and validate enum values."""

    operator = authenticated_user_factory(
        role=UserRole.OPERATOR,
    )
    headers = operator["headers"]

    create_incident(
        client,
        headers,
        title="Orders API outage",
        description="Customer order requests are failing.",
        service_name="orders-api",
        severity="critical",
    )
    investigating_incident = create_incident(
        client,
        headers,
        title="Checkout processing delay",
        description="Checkout jobs require additional processing time.",
        service_name="checkout-worker",
        severity="high",
    )
    create_incident(
        client,
        headers,
        title="Search indexing delay",
        description="New products are waiting to be indexed.",
        service_name="search-worker",
        severity="high",
    )

    update_response = client.patch(
        f"/api/incidents/{investigating_incident['id']}",
        headers=headers,
        json={"status": "investigating"},
    )

    assert update_response.status_code == 200

    filtered_response = client.get(
        "/api/incidents",
        headers=headers,
        params={
            "status": "investigating",
            "severity": "high",
        },
    )

    invalid_status_response = client.get(
        "/api/incidents",
        headers=headers,
        params={"status": "degraded"},
    )
    invalid_severity_response = client.get(
        "/api/incidents",
        headers=headers,
        params={"severity": "urgent"},
    )

    assert filtered_response.status_code == 200
    assert [
        incident["id"]
        for incident in filtered_response.json()
    ] == [investigating_incident["id"]]

    assert invalid_status_response.status_code == 422
    assert invalid_severity_response.status_code == 422
