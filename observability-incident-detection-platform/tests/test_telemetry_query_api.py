import pytest
from httpx2 import AsyncClient

pytestmark = pytest.mark.asyncio


async def seed_telemetry(api_client: AsyncClient) -> None:
    services = [
        {
            "name": "checkout-service",
            "environment": "development",
        },
        {
            "name": "payment-service",
            "environment": "production",
        },
    ]

    for service in services:
        response = await api_client.post(
            "/api/v1/services",
            json=service,
        )
        assert response.status_code == 201

    response = await api_client.post(
        "/api/v1/telemetry",
        json={
            "items": [
                {
                    "type": "metric",
                    "service": "checkout-service",
                    "environment": "development",
                    "source": "checkout-instance-1",
                    "timestamp": "2026-09-15T10:00:00Z",
                    "name": "cpu_usage",
                    "value": 72.5,
                    "unit": "percent",
                },
                {
                    "type": "log",
                    "service": "checkout-service",
                    "environment": "development",
                    "source": "checkout-instance-2",
                    "timestamp": "2026-09-15T11:00:00Z",
                    "level": "error",
                    "message": "Payment provider timed out",
                },
                {
                    "type": "event",
                    "service": "payment-service",
                    "environment": "production",
                    "source": "payment-instance-1",
                    "timestamp": "2026-09-15T12:00:00Z",
                    "name": "service_restart",
                    "severity": "warning",
                },
            ]
        },
    )

    assert response.status_code == 202


async def test_query_returns_telemetry_newest_first(
    api_client: AsyncClient,
) -> None:
    await seed_telemetry(api_client)

    response = await api_client.get("/api/v1/telemetry")
    payload = response.json()

    assert response.status_code == 200
    assert payload["total"] == 3
    assert payload["limit"] == 50
    assert payload["offset"] == 0
    assert [item["type"] for item in payload["items"]] == [
        "event",
        "log",
        "metric",
    ]


async def test_query_filters_telemetry(
    api_client: AsyncClient,
) -> None:
    await seed_telemetry(api_client)

    response = await api_client.get(
        "/api/v1/telemetry",
        params={
            "service": "checkout-service",
            "environment": "development",
            "type": "metric",
            "source": "checkout-instance-1",
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["total"] == 1
    assert len(payload["items"]) == 1

    item = payload["items"][0]
    assert item["service"] == "checkout-service"
    assert item["environment"] == "development"
    assert item["type"] == "metric"
    assert item["source"] == "checkout-instance-1"


async def test_query_filters_by_observed_time_range(
    api_client: AsyncClient,
) -> None:
    await seed_telemetry(api_client)

    response = await api_client.get(
        "/api/v1/telemetry",
        params={
            "observed_from": "2026-09-15T10:30:00Z",
            "observed_to": "2026-09-15T11:30:00Z",
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["total"] == 1
    assert payload["items"][0]["type"] == "log"


async def test_query_applies_pagination(
    api_client: AsyncClient,
) -> None:
    await seed_telemetry(api_client)

    response = await api_client.get(
        "/api/v1/telemetry",
        params={
            "limit": 1,
            "offset": 1,
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["total"] == 3
    assert payload["limit"] == 1
    assert payload["offset"] == 1
    assert len(payload["items"]) == 1
    assert payload["items"][0]["type"] == "log"


async def test_query_rejects_invalid_time_range(
    api_client: AsyncClient,
) -> None:
    response = await api_client.get(
        "/api/v1/telemetry",
        params={
            "observed_from": "2026-09-15T12:00:00Z",
            "observed_to": "2026-09-15T10:00:00Z",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "observed_from must be earlier than or equal to observed_to"
    )


@pytest.mark.parametrize("limit", [0, 101])
async def test_query_rejects_invalid_limit(
    api_client: AsyncClient,
    limit: int,
) -> None:
    response = await api_client.get(
        "/api/v1/telemetry",
        params={"limit": limit},
    )

    assert response.status_code == 422
