from uuid import uuid4

import pytest
from httpx2 import AsyncClient

pytestmark = pytest.mark.asyncio


async def seed_incident(api_client: AsyncClient) -> str:
    response = await api_client.post(
        "/api/v1/services",
        json={
            "name": "checkout-service",
            "environment": "production",
        },
    )
    assert response.status_code == 201

    response = await api_client.post(
        "/api/v1/telemetry",
        json={
            "items": [
                {
                    "type": "metric",
                    "service": "checkout-service",
                    "environment": "production",
                    "source": "checkout-instance-1",
                    "name": "cpu_usage",
                    "value": 96.0,
                    "unit": "percent",
                },
                {
                    "type": "log",
                    "service": "checkout-service",
                    "environment": "production",
                    "source": "checkout-instance-1",
                    "level": "error",
                    "message": "A recoverable checkout error occurred",
                },
            ]
        },
    )
    payload = response.json()

    assert response.status_code == 202
    assert payload["detected_anomaly_count"] == 2
    assert payload["created_incident_count"] == 1
    assert len(payload["incident_ids"]) == 1

    return payload["incident_ids"][0]


async def test_query_returns_open_incident(
    api_client: AsyncClient,
) -> None:
    incident_id = await seed_incident(api_client)

    response = await api_client.get("/api/v1/incidents")
    payload = response.json()

    assert response.status_code == 200
    assert payload["total"] == 1
    assert payload["items"][0]["id"] == incident_id
    assert payload["items"][0]["status"] == "open"
    assert payload["items"][0]["severity"] == "critical"


async def test_get_incident_by_id(
    api_client: AsyncClient,
) -> None:
    incident_id = await seed_incident(api_client)

    response = await api_client.get(f"/api/v1/incidents/{incident_id}")
    payload = response.json()

    assert response.status_code == 200
    assert payload["id"] == incident_id
    assert payload["service"] == "checkout-service"
    assert payload["environment"] == "production"
    assert payload["trigger_anomaly_id"]


async def test_query_filters_incidents(
    api_client: AsyncClient,
) -> None:
    await seed_incident(api_client)

    response = await api_client.get(
        "/api/v1/incidents",
        params={
            "service": "checkout-service",
            "environment": "production",
            "status": "open",
            "severity": "critical",
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["total"] == 1
    assert len(payload["items"]) == 1


async def test_acknowledge_open_incident(
    api_client: AsyncClient,
) -> None:
    incident_id = await seed_incident(api_client)

    response = await api_client.patch(
        f"/api/v1/incidents/{incident_id}/acknowledge",
        json={"acknowledged_by": "aj"},
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "acknowledged"
    assert payload["acknowledged_by"] == "aj"
    assert payload["acknowledged_at"] is not None
    assert payload["resolved_at"] is None


async def test_resolve_acknowledged_incident(
    api_client: AsyncClient,
) -> None:
    incident_id = await seed_incident(api_client)

    acknowledge_response = await api_client.patch(
        f"/api/v1/incidents/{incident_id}/acknowledge",
        json={"acknowledged_by": "aj"},
    )
    assert acknowledge_response.status_code == 200

    response = await api_client.patch(
        f"/api/v1/incidents/{incident_id}/resolve",
        json={
            "resolved_by": "aj",
            "resolution_summary": "Restarted the checkout worker",
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "resolved"
    assert payload["resolved_by"] == "aj"
    assert payload["resolved_at"] is not None
    assert payload["resolution_summary"] == ("Restarted the checkout worker")


async def test_resolve_open_incident_directly(
    api_client: AsyncClient,
) -> None:
    incident_id = await seed_incident(api_client)

    response = await api_client.patch(
        f"/api/v1/incidents/{incident_id}/resolve",
        json={
            "resolved_by": "automation",
            "resolution_summary": "Recovered automatically",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "resolved"


async def test_resolved_incident_cannot_be_acknowledged(
    api_client: AsyncClient,
) -> None:
    incident_id = await seed_incident(api_client)

    resolve_response = await api_client.patch(
        f"/api/v1/incidents/{incident_id}/resolve",
        json={
            "resolved_by": "aj",
            "resolution_summary": "Issue resolved",
        },
    )
    assert resolve_response.status_code == 200

    response = await api_client.patch(
        f"/api/v1/incidents/{incident_id}/acknowledge",
        json={"acknowledged_by": "aj"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Incident in status 'resolved' cannot be acknowledged"
    )


async def test_get_unknown_incident_returns_not_found(
    api_client: AsyncClient,
) -> None:
    incident_id = uuid4()

    response = await api_client.get(f"/api/v1/incidents/{incident_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == (f"Incident '{incident_id}' was not found")


async def test_query_rejects_invalid_created_time_range(
    api_client: AsyncClient,
) -> None:
    response = await api_client.get(
        "/api/v1/incidents",
        params={
            "created_from": "2026-09-16T12:00:00Z",
            "created_to": "2026-09-16T10:00:00Z",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "created_from must be earlier than or equal to created_to"
    )


@pytest.mark.parametrize(
    ("parameter", "value"),
    [
        ("limit", 0),
        ("offset", -1),
        ("status", "unknown"),
    ],
)
async def test_query_rejects_invalid_parameters(
    api_client: AsyncClient,
    parameter: str,
    value: int | str,
) -> None:
    response = await api_client.get(
        "/api/v1/incidents",
        params={parameter: value},
    )

    assert response.status_code == 422


async def test_openapi_schema_contains_incident_endpoints(
    api_client: AsyncClient,
) -> None:
    response = await api_client.get("/openapi.json")
    paths = response.json()["paths"]

    assert response.status_code == 200
    assert "/api/v1/incidents" in paths
    assert "/api/v1/incidents/{incident_id}" in paths
    assert "/api/v1/incidents/{incident_id}/acknowledge" in paths
    assert "/api/v1/incidents/{incident_id}/resolve" in paths
