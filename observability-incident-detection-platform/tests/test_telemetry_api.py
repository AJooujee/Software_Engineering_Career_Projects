from datetime import datetime

import pytest
from httpx2 import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from observability_platform.db.models import (
    AnomalyRecord,
    IncidentRecord,
    TelemetryRecord,
)

pytestmark = pytest.mark.asyncio


async def register_service(
    api_client: AsyncClient,
    *,
    name: str = "checkout-service",
    environment: str = "development",
) -> None:
    response = await api_client.post(
        "/api/v1/services",
        json={
            "name": name,
            "environment": environment,
        },
    )

    assert response.status_code == 201


async def test_ingest_mixed_telemetry_batch(
    api_client: AsyncClient,
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await register_service(api_client)

    response = await api_client.post(
        "/api/v1/telemetry",
        json={
            "items": [
                {
                    "type": "metric",
                    "service": "checkout-service",
                    "environment": "development",
                    "source": "checkout-instance-1",
                    "name": "cpu_usage",
                    "value": 72.5,
                    "unit": "percent",
                },
                {
                    "type": "log",
                    "service": "checkout-service",
                    "environment": "development",
                    "source": "checkout-instance-1",
                    "level": "error",
                    "message": "Payment provider timed out",
                },
                {
                    "type": "event",
                    "service": "checkout-service",
                    "environment": "development",
                    "source": "checkout-instance-1",
                    "name": "service_restart",
                    "severity": "warning",
                    "description": "Instance restarted",
                },
            ]
        },
    )

    payload = response.json()

    assert response.status_code == 202
    assert payload["accepted_count"] == 3
    assert len(payload["telemetry_ids"]) == 3
    assert payload["detected_anomaly_count"] == 1
    assert len(payload["anomaly_ids"]) == 1
    assert len(set(payload["telemetry_ids"])) == 3
    assert payload["created_incident_count"] == 0
    assert payload["incident_ids"] == []
    assert datetime.fromisoformat(payload["received_at"]).tzinfo is not None
    assert "X-Request-ID" in response.headers
    async with test_session_factory() as session:
        telemetry_result = await session.execute(
            select(func.count()).select_from(TelemetryRecord)
        )
        anomaly_result = await session.execute(
            select(func.count()).select_from(AnomalyRecord)
        )
        incident_result = await session.execute(
            select(func.count()).select_from(IncidentRecord)
        )

    assert telemetry_result.scalar_one() == 3
    assert anomaly_result.scalar_one() == 1
    assert incident_result.scalar_one() == 0


async def test_ingest_rejects_unregistered_service(
    api_client: AsyncClient,
) -> None:
    response = await api_client.post(
        "/api/v1/telemetry",
        json={
            "items": [
                {
                    "type": "metric",
                    "service": "unknown-service",
                    "source": "unknown-instance-1",
                    "name": "cpu_usage",
                    "value": 50.0,
                }
            ]
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Service 'unknown-service' is not registered in environment 'development'"
    )


async def test_ingest_rejects_empty_batch(
    api_client: AsyncClient,
) -> None:
    response = await api_client.post(
        "/api/v1/telemetry",
        json={"items": []},
    )

    assert response.status_code == 422


async def test_ingest_rejects_unknown_telemetry_type(
    api_client: AsyncClient,
) -> None:
    response = await api_client.post(
        "/api/v1/telemetry",
        json={
            "items": [
                {
                    "type": "trace",
                    "service": "checkout-service",
                    "source": "checkout-instance-1",
                }
            ]
        },
    )

    assert response.status_code == 422


async def test_ingest_rejects_invalid_metric_value(
    api_client: AsyncClient,
) -> None:
    response = await api_client.post(
        "/api/v1/telemetry",
        json={
            "items": [
                {
                    "type": "metric",
                    "service": "checkout-service",
                    "source": "checkout-instance-1",
                    "name": "cpu_usage",
                    "value": "not-a-number",
                }
            ]
        },
    )

    assert response.status_code == 422


async def test_openapi_schema_contains_telemetry_endpoint(
    api_client: AsyncClient,
) -> None:
    response = await api_client.get("/openapi.json")

    assert response.status_code == 200
    assert "/api/v1/telemetry" in response.json()["paths"]
    assert "post" in response.json()["paths"]["/api/v1/telemetry"]
    assert "get" in response.json()["paths"]["/api/v1/telemetry"]


async def test_ingest_critical_anomalies_create_incidents(
    api_client: AsyncClient,
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await register_service(api_client)

    response = await api_client.post(
        "/api/v1/telemetry",
        json={
            "items": [
                {
                    "type": "metric",
                    "service": "checkout-service",
                    "environment": "development",
                    "source": "checkout-instance-1",
                    "name": "cpu_usage",
                    "value": 95.0,
                    "unit": "percent",
                },
                {
                    "type": "log",
                    "service": "checkout-service",
                    "environment": "development",
                    "source": "checkout-instance-1",
                    "level": "critical",
                    "message": "Checkout database is unavailable",
                },
            ]
        },
    )
    payload = response.json()

    assert response.status_code == 202
    assert payload["accepted_count"] == 2
    assert payload["detected_anomaly_count"] == 2
    assert payload["created_incident_count"] == 2
    assert len(payload["incident_ids"]) == 2

    async with test_session_factory() as session:
        result = await session.execute(
            select(IncidentRecord).order_by(IncidentRecord.created_at)
        )
        incidents = list(result.scalars().all())

    assert len(incidents) == 2
    assert {str(incident.id) for incident in incidents} == set(payload["incident_ids"])
    assert all(incident.status == "open" for incident in incidents)
    assert all(incident.severity == "critical" for incident in incidents)
    assert len({incident.trigger_anomaly_id for incident in incidents}) == 2
