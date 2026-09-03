"""Integration tests for the operational incident REST API."""

from uuid import UUID, uuid4

from fastapi.testclient import TestClient


def test_incident_crud_lifecycle(client: TestClient) -> None:
    """Create, list, retrieve, update, and delete an incident."""

    create_response = client.post(
        "/api/incidents",
        json={
            "title": "Orders API outage",
            "description": "Customer requests are returning errors.",
            "service_name": "orders-api",
            "severity": "critical",
        },
    )

    assert create_response.status_code == 201

    created_incident = create_response.json()
    incident_id = created_incident["id"]

    # Confirm the API generated a valid UUID and default status.
    UUID(incident_id)
    assert created_incident["title"] == "Orders API outage"
    assert created_incident["severity"] == "critical"
    assert created_incident["status"] == "open"
    assert created_incident["created_at"]
    assert created_incident["updated_at"]

    list_response = client.get("/api/incidents")

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["id"] == incident_id

    retrieve_response = client.get(f"/api/incidents/{incident_id}")

    assert retrieve_response.status_code == 200
    assert retrieve_response.json()["id"] == incident_id

    update_response = client.patch(
        f"/api/incidents/{incident_id}",
        json={
            "status": "investigating",
            "description": "The operations team is investigating the outage.",
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["status"] == "investigating"
    assert (
        update_response.json()["description"]
        == "The operations team is investigating the outage."
    )

    delete_response = client.delete(f"/api/incidents/{incident_id}")

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    missing_response = client.get(f"/api/incidents/{incident_id}")

    assert missing_response.status_code == 404


def test_missing_incident_returns_not_found(client: TestClient) -> None:
    """Return a descriptive 404 response for an unknown incident."""

    missing_incident_id = uuid4()

    response = client.get(f"/api/incidents/{missing_incident_id}")

    assert response.status_code == 404
    assert response.json() == {
        "detail": f"Incident '{missing_incident_id}' was not found."
    }


def test_incident_validation_rejects_invalid_input(
    client: TestClient,
) -> None:
    """Reject incident payloads and pagination outside allowed limits."""

    invalid_incident_response = client.post(
        "/api/incidents",
        json={
            "title": "X",
            "description": "",
            "service_name": "A",
            "severity": "urgent",
        },
    )

    assert invalid_incident_response.status_code == 422

    invalid_pagination_response = client.get(
        "/api/incidents",
        params={"limit": 101},
    )

    assert invalid_pagination_response.status_code == 422
