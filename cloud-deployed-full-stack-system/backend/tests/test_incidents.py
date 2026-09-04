"""Integration tests for incident authentication and authorization."""

from collections.abc import Callable
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.models.user import UserRole


def incident_payload() -> dict[str, str]:
    """Return a valid incident creation payload."""

    return {
        "title": "Orders API outage",
        "description": "Customer requests are returning errors.",
        "service_name": "orders-api",
        "severity": "critical",
    }


def test_unauthenticated_incident_access_is_rejected(
    client: TestClient,
) -> None:
    """Require a bearer token before returning incident data."""

    response = client.get("/api/incidents")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Not authenticated"
    }


def test_viewer_can_read_but_cannot_create_incidents(
    client: TestClient,
    authenticated_user_factory: Callable[..., dict[str, object]],
) -> None:
    """Allow viewers to read incidents without modifying them."""

    viewer = authenticated_user_factory(
        role=UserRole.VIEWER,
    )

    list_response = client.get(
        "/api/incidents",
        headers=viewer["headers"],
    )

    create_response = client.post(
        "/api/incidents",
        headers=viewer["headers"],
        json=incident_payload(),
    )

    assert list_response.status_code == 200
    assert list_response.json() == []

    assert create_response.status_code == 403
    assert create_response.json() == {
        "detail": "Insufficient permissions."
    }


def test_operator_can_create_and_update_but_cannot_delete(
    client: TestClient,
    authenticated_user_factory: Callable[..., dict[str, object]],
) -> None:
    """Enforce the incident permissions assigned to operators."""

    operator = authenticated_user_factory(
        role=UserRole.OPERATOR,
    )

    create_response = client.post(
        "/api/incidents",
        headers=operator["headers"],
        json=incident_payload(),
    )

    assert create_response.status_code == 201

    created_incident = create_response.json()
    incident_id = created_incident["id"]

    UUID(incident_id)
    assert created_incident["status"] == "open"
    assert created_incident["severity"] == "critical"

    list_response = client.get(
        "/api/incidents",
        headers=operator["headers"],
    )

    retrieve_response = client.get(
        f"/api/incidents/{incident_id}",
        headers=operator["headers"],
    )

    update_response = client.patch(
        f"/api/incidents/{incident_id}",
        headers=operator["headers"],
        json={
            "status": "investigating",
            "description": (
                "The operations team is investigating the outage."
            ),
        },
    )

    delete_response = client.delete(
        f"/api/incidents/{incident_id}",
        headers=operator["headers"],
    )

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    assert retrieve_response.status_code == 200
    assert retrieve_response.json()["id"] == incident_id

    assert update_response.status_code == 200
    assert update_response.json()["status"] == "investigating"

    assert delete_response.status_code == 403
    assert delete_response.json() == {
        "detail": "Insufficient permissions."
    }


def test_admin_can_delete_incidents(
    client: TestClient,
    authenticated_user_factory: Callable[..., dict[str, object]],
) -> None:
    """Allow administrators to complete the full incident lifecycle."""

    administrator = authenticated_user_factory(
        role=UserRole.ADMIN,
    )

    create_response = client.post(
        "/api/incidents",
        headers=administrator["headers"],
        json=incident_payload(),
    )

    assert create_response.status_code == 201

    incident_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/api/incidents/{incident_id}",
        headers=administrator["headers"],
    )

    missing_response = client.get(
        f"/api/incidents/{incident_id}",
        headers=administrator["headers"],
    )

    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert missing_response.status_code == 404


def test_missing_incident_returns_not_found(
    client: TestClient,
    authenticated_user_factory: Callable[..., dict[str, object]],
) -> None:
    """Return a descriptive 404 to an authenticated user."""

    viewer = authenticated_user_factory(
        role=UserRole.VIEWER,
    )
    missing_incident_id = uuid4()

    response = client.get(
        f"/api/incidents/{missing_incident_id}",
        headers=viewer["headers"],
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": f"Incident '{missing_incident_id}' was not found."
    }


def test_incident_validation_rejects_invalid_input(
    client: TestClient,
    authenticated_user_factory: Callable[..., dict[str, object]],
) -> None:
    """Reject incident payloads and pagination outside allowed limits."""

    operator = authenticated_user_factory(
        role=UserRole.OPERATOR,
    )

    invalid_incident_response = client.post(
        "/api/incidents",
        headers=operator["headers"],
        json={
            "title": "X",
            "description": "",
            "service_name": "A",
            "severity": "urgent",
        },
    )

    invalid_pagination_response = client.get(
        "/api/incidents",
        headers=operator["headers"],
        params={"limit": 101},
    )

    assert invalid_incident_response.status_code == 422
    assert invalid_pagination_response.status_code == 422
