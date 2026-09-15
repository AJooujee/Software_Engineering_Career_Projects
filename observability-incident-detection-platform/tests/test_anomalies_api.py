import pytest
from httpx2 import AsyncClient

pytestmark = pytest.mark.asyncio


async def seed_anomalies(api_client: AsyncClient) -> None:
    response = await api_client.post(
        "/api/v1/services",
        json={
            "name": "payment-service",
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
                    "service": "payment-service",
                    "environment": "production",
                    "source": "payment-instance-1",
                    "name": "cpu_usage",
                    "value": 95.0,
                    "unit": "percent",
                },
                {
                    "type": "log",
                    "service": "payment-service",
                    "environment": "production",
                    "source": "payment-instance-1",
                    "level": "error",
                    "message": "Payment request failed",
                },
                {
                    "type": "event",
                    "service": "payment-service",
                    "environment": "production",
                    "source": "payment-instance-2",
                    "name": "provider_outage",
                    "severity": "critical",
                    "description": "Payment provider is unavailable",
                },
            ]
        },
    )

    payload = response.json()

    assert response.status_code == 202
    assert payload["accepted_count"] == 3
    assert payload["detected_anomaly_count"] == 3
    assert len(payload["anomaly_ids"]) == 3


async def test_query_returns_detected_anomalies(
    api_client: AsyncClient,
) -> None:
    await seed_anomalies(api_client)

    response = await api_client.get("/api/v1/anomalies")
    payload = response.json()

    assert response.status_code == 200
    assert payload["total"] == 3
    assert payload["limit"] == 50
    assert payload["offset"] == 0
    assert len(payload["items"]) == 3
    assert {item["rule_id"] for item in payload["items"]} == {
        "metric.cpu_usage.high",
        "log.level.error",
        "event.severity.critical",
    }


async def test_query_filters_anomalies_by_severity(
    api_client: AsyncClient,
) -> None:
    await seed_anomalies(api_client)

    response = await api_client.get(
        "/api/v1/anomalies",
        params={"severity": "critical"},
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["total"] == 2
    assert all(item["severity"] == "critical" for item in payload["items"])


async def test_query_filters_anomalies_by_identity_and_rule(
    api_client: AsyncClient,
) -> None:
    await seed_anomalies(api_client)

    response = await api_client.get(
        "/api/v1/anomalies",
        params={
            "service": "payment-service",
            "environment": "production",
            "category": "log_severity",
            "rule_id": "log.level.error",
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["total"] == 1

    item = payload["items"][0]
    assert item["service"] == "payment-service"
    assert item["environment"] == "production"
    assert item["category"] == "log_severity"
    assert item["rule_id"] == "log.level.error"


async def test_query_applies_anomaly_pagination(
    api_client: AsyncClient,
) -> None:
    await seed_anomalies(api_client)

    response = await api_client.get(
        "/api/v1/anomalies",
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


async def test_query_rejects_invalid_detected_time_range(
    api_client: AsyncClient,
) -> None:
    response = await api_client.get(
        "/api/v1/anomalies",
        params={
            "detected_from": "2026-09-15T12:00:00Z",
            "detected_to": "2026-09-15T10:00:00Z",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "detected_from must be earlier than or equal to detected_to"
    )


@pytest.mark.parametrize(
    ("parameter", "value"),
    [
        ("limit", 0),
        ("offset", -1),
        ("severity", "unknown"),
    ],
)
async def test_query_rejects_invalid_parameters(
    api_client: AsyncClient,
    parameter: str,
    value: int | str,
) -> None:
    response = await api_client.get(
        "/api/v1/anomalies",
        params={parameter: value},
    )

    assert response.status_code == 422


async def test_openapi_schema_contains_anomaly_endpoint(
    api_client: AsyncClient,
) -> None:
    response = await api_client.get("/openapi.json")

    assert response.status_code == 200
    assert "/api/v1/anomalies" in response.json()["paths"]
    assert "get" in response.json()["paths"]["/api/v1/anomalies"]
