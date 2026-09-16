from uuid import uuid4

import pytest
from httpx2 import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from observability_platform.db.models import (
    CorrelationIncidentRecord,
    CorrelationRecord,
)

pytestmark = pytest.mark.asyncio


async def register_service(api_client: AsyncClient) -> None:
    response = await api_client.post(
        "/api/v1/services",
        json={
            "name": "payment-service",
            "environment": "production",
        },
    )

    assert response.status_code == 201


async def seed_correlatable_incidents(
    api_client: AsyncClient,
) -> list[str]:
    await register_service(api_client)

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
                    "value": 96.0,
                    "unit": "percent",
                },
                {
                    "type": "log",
                    "service": "payment-service",
                    "environment": "production",
                    "source": "payment-instance-1",
                    "level": "critical",
                    "message": "Payment database connection failed",
                },
            ]
        },
    )
    payload = response.json()

    assert response.status_code == 202
    assert payload["detected_anomaly_count"] == 2
    assert payload["created_incident_count"] == 2
    assert len(payload["incident_ids"]) == 2

    return payload["incident_ids"]


async def create_correlation(
    api_client: AsyncClient,
) -> dict:
    await seed_correlatable_incidents(api_client)

    response = await api_client.post(
        "/api/v1/correlations/analyze",
        json={
            "service": "payment-service",
            "environment": "production",
            "window_minutes": 15,
            "minimum_incidents": 2,
        },
    )

    assert response.status_code == 201
    return response.json()


async def test_analyze_correlates_incidents_and_persists_records(
    api_client: AsyncClient,
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    incident_ids = await seed_correlatable_incidents(api_client)

    response = await api_client.post(
        "/api/v1/correlations/analyze",
        json={
            "service": "payment-service",
            "environment": "production",
            "window_minutes": 15,
            "minimum_incidents": 2,
        },
    )
    payload = response.json()

    assert response.status_code == 201
    assert payload["service"] == "payment-service"
    assert payload["environment"] == "production"
    assert payload["status"] == "active"
    assert payload["incident_count"] == 2
    assert set(payload["incident_ids"]) == set(incident_ids)
    assert payload["root_cause"]["incident_id"] in incident_ids
    assert 0.0 <= payload["root_cause"]["confidence_score"] <= 1.0
    assert payload["root_cause"]["reasons"]
    assert "Correlated 2 incidents" in payload["summary"]

    async with test_session_factory() as session:
        correlation_result = await session.execute(
            select(func.count()).select_from(CorrelationRecord)
        )
        link_result = await session.execute(
            select(func.count()).select_from(CorrelationIncidentRecord)
        )

    assert correlation_result.scalar_one() == 1
    assert link_result.scalar_one() == 2


async def test_analyze_rejects_insufficient_incidents(
    api_client: AsyncClient,
) -> None:
    await register_service(api_client)

    ingest_response = await api_client.post(
        "/api/v1/telemetry",
        json={
            "items": [
                {
                    "type": "metric",
                    "service": "payment-service",
                    "environment": "production",
                    "source": "payment-instance-1",
                    "name": "cpu_usage",
                    "value": 97.0,
                    "unit": "percent",
                }
            ]
        },
    )
    assert ingest_response.status_code == 202
    assert ingest_response.json()["created_incident_count"] == 1

    response = await api_client.post(
        "/api/v1/correlations/analyze",
        json={
            "service": "payment-service",
            "environment": "production",
            "minimum_incidents": 2,
        },
    )
    payload = response.json()

    assert response.status_code == 422
    assert "Found 1 uncorrelated incidents" in payload["detail"]
    assert "at least 2 are required" in payload["detail"]


async def test_analyze_does_not_reuse_correlated_incidents(
    api_client: AsyncClient,
) -> None:
    await seed_correlatable_incidents(api_client)

    first_response = await api_client.post(
        "/api/v1/correlations/analyze",
        json={
            "service": "payment-service",
            "environment": "production",
            "minimum_incidents": 2,
        },
    )
    assert first_response.status_code == 201

    second_response = await api_client.post(
        "/api/v1/correlations/analyze",
        json={
            "service": "payment-service",
            "environment": "production",
            "minimum_incidents": 2,
        },
    )
    payload = second_response.json()

    assert second_response.status_code == 422
    assert "Found 0 uncorrelated incidents" in payload["detail"]


async def test_get_correlation_by_id(
    api_client: AsyncClient,
) -> None:
    created = await create_correlation(api_client)

    response = await api_client.get(f"/api/v1/correlations/{created['id']}")
    payload = response.json()

    assert response.status_code == 200
    assert payload["id"] == created["id"]
    assert payload["service"] == "payment-service"
    assert payload["environment"] == "production"
    assert payload["incident_count"] == 2
    assert set(payload["incident_ids"]) == set(created["incident_ids"])
    assert payload["root_cause"] == created["root_cause"]


async def test_get_correlation_returns_not_found(
    api_client: AsyncClient,
) -> None:
    correlation_id = uuid4()

    response = await api_client.get(f"/api/v1/correlations/{correlation_id}")
    payload = response.json()

    assert response.status_code == 404
    assert str(correlation_id) in payload["detail"]


async def test_query_correlations_with_filters(
    api_client: AsyncClient,
) -> None:
    created = await create_correlation(api_client)

    response = await api_client.get(
        "/api/v1/correlations",
        params={
            "service": "payment-service",
            "environment": "production",
            "status": "active",
            "limit": 10,
            "offset": 0,
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["total"] == 1
    assert payload["limit"] == 10
    assert payload["offset"] == 0
    assert len(payload["items"]) == 1
    assert payload["items"][0]["id"] == created["id"]


async def test_query_correlations_returns_empty_for_nonmatching_filter(
    api_client: AsyncClient,
) -> None:
    await create_correlation(api_client)

    response = await api_client.get(
        "/api/v1/correlations",
        params={
            "service": "inventory-service",
            "environment": "production",
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["total"] == 0
    assert payload["items"] == []
