"""Integration tests for metric dashboard summary APIs."""

from datetime import UTC, datetime

import pytest
from httpx2 import AsyncClient

pytestmark = pytest.mark.asyncio

# Use one registered service identity consistently across dashboard tests.
SERVICE_NAME = "dashboard-service"
ENVIRONMENT = "production"
METRIC_NAME = "request_latency"


def parse_api_datetime(value: str) -> datetime:
    """Normalize datetime strings returned by PostgreSQL and SQLite."""

    # Convert the JSON UTC suffix into an offset Python can parse.
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))

    # SQLite may remove timezone information during integration tests.
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)

    # Normalize timezone-aware values to UTC before comparison.
    return parsed.astimezone(UTC)


async def register_dashboard_service(
    api_client: AsyncClient,
) -> None:
    """Register the monitored service that owns dashboard telemetry."""

    # Arrange and act: create the service before ingesting metric records.
    response = await api_client.post(
        "/api/v1/services",
        json={
            "name": SERVICE_NAME,
            "environment": ENVIRONMENT,
            "description": "Service used by metric dashboard tests",
        },
    )

    # Assert: telemetry ingestion requires successful service registration.
    assert response.status_code == 201


def metric_item(
    *,
    value: float,
    timestamp: str,
    source: str = "dashboard-instance-1",
    unit: str = "milliseconds",
    name: str = METRIC_NAME,
) -> dict:
    """Build one metric telemetry item with explicit dashboard dimensions."""

    # Return the same validated telemetry shape used by production ingestion.
    return {
        "type": "metric",
        "service": SERVICE_NAME,
        "environment": ENVIRONMENT,
        "source": source,
        "timestamp": timestamp,
        "name": name,
        "value": value,
        "unit": unit,
        "attributes": {
            "region": "us-east",
        },
    }


async def seed_dashboard_metrics(
    api_client: AsyncClient,
) -> None:
    """Persist chronological metric samples from multiple runtime sources."""

    # Arrange: register the service referenced by every metric item.
    await register_dashboard_service(api_client)

    # Include four target samples, one unrelated metric, and two sources. The
    # unrelated metric verifies filtering by payload metric name.
    items = [
        metric_item(
            value=10.0,
            timestamp="2026-09-16T18:00:00Z",
        ),
        metric_item(
            value=20.0,
            timestamp="2026-09-16T18:01:00Z",
            source="dashboard-instance-2",
        ),
        metric_item(
            value=30.0,
            timestamp="2026-09-16T18:02:00Z",
        ),
        metric_item(
            value=40.0,
            timestamp="2026-09-16T18:03:00Z",
            source="dashboard-instance-2",
        ),
        metric_item(
            value=75.0,
            timestamp="2026-09-16T18:02:30Z",
            name="memory_usage",
            unit="percent",
        ),
    ]

    # Act: persist all samples through the production telemetry endpoint.
    response = await api_client.post(
        "/api/v1/telemetry",
        json={"items": items},
    )
    payload = response.json()

    # Assert: all telemetry records were accepted atomically.
    assert response.status_code == 202
    assert payload["accepted_count"] == len(items)


def dashboard_params() -> dict:
    """Build a bounded query that includes every seeded target sample."""

    # Explicit UTC boundaries keep tests deterministic and independent of the
    # machine's current clock.
    return {
        "service": SERVICE_NAME,
        "environment": ENVIRONMENT,
        "metric": METRIC_NAME,
        "observed_from": "2026-09-16T17:59:00Z",
        "observed_to": "2026-09-16T18:04:00Z",
    }


async def test_metric_summary_returns_statistics_and_points(
    api_client: AsyncClient,
) -> None:
    """Aggregate matching samples into statistics and chronological points."""

    # Arrange: persist four request-latency samples and one unrelated metric.
    await seed_dashboard_metrics(api_client)

    # Act: request the complete request-latency dashboard summary.
    response = await api_client.get(
        "/api/v1/dashboard/metrics/summary",
        params=dashboard_params(),
    )
    payload = response.json()

    # Assert: the selected service and metric dimensions are preserved.
    assert response.status_code == 200
    assert payload["service"] == SERVICE_NAME
    assert payload["environment"] == ENVIRONMENT
    assert payload["metric_name"] == METRIC_NAME
    assert payload["unit"] == "milliseconds"

    # Assert: only the four target samples contribute to aggregation.
    assert payload["sample_count"] == 4
    assert payload["minimum_value"] == 10.0
    assert payload["maximum_value"] == 40.0
    assert payload["average_value"] == 25.0

    # The nearest-rank p95 of four ordered values selects the maximum value.
    assert payload["p95_value"] == 40.0

    # The newest matching observation supplies the latest-value fields.
    assert payload["latest_value"] == 40.0
    # Parse the API timestamp so SQLite and PostgreSQL serialization formats
    # are tested by semantic time value rather than an optional "Z" suffix.
    assert parse_api_datetime(payload["latest_observed_at"]) == datetime(
        2026,
        9,
        16,
        18,
        3,
        tzinfo=UTC,
    )

    # Sources are unique and sorted for deterministic dashboard output.
    assert payload["sources"] == [
        "dashboard-instance-1",
        "dashboard-instance-2",
    ]

    # Time-series points must remain in chronological observation order.
    assert [point["value"] for point in payload["points"]] == [
        10.0,
        20.0,
        30.0,
        40.0,
    ]


async def test_metric_summary_filters_by_source(
    api_client: AsyncClient,
) -> None:
    """Aggregate only samples emitted by the requested runtime source."""

    # Arrange: seed samples from two runtime instances.
    await seed_dashboard_metrics(api_client)
    params = dashboard_params()

    # Restrict the dashboard to the first runtime instance.
    params["source"] = "dashboard-instance-1"

    # Act: request a source-specific metric summary.
    response = await api_client.get(
        "/api/v1/dashboard/metrics/summary",
        params=params,
    )
    payload = response.json()

    # Assert: only values 10 and 30 belong to the selected source.
    assert response.status_code == 200
    assert payload["sample_count"] == 2
    assert payload["sources"] == ["dashboard-instance-1"]
    assert payload["minimum_value"] == 10.0
    assert payload["maximum_value"] == 30.0
    assert payload["average_value"] == 20.0
    assert payload["latest_value"] == 30.0


async def test_metric_summary_filters_by_time_range(
    api_client: AsyncClient,
) -> None:
    """Aggregate only samples inside inclusive observation boundaries."""

    # Arrange: seed four chronological target samples.
    await seed_dashboard_metrics(api_client)
    params = dashboard_params()

    # Narrow the interval to the final two target observations.
    params["observed_from"] = "2026-09-16T18:02:00Z"
    params["observed_to"] = "2026-09-16T18:03:00Z"

    # Act: query the narrowed dashboard interval.
    response = await api_client.get(
        "/api/v1/dashboard/metrics/summary",
        params=params,
    )
    payload = response.json()

    # Assert: inclusive boundaries retain values at both endpoints.
    assert response.status_code == 200
    assert payload["sample_count"] == 2
    assert [point["value"] for point in payload["points"]] == [
        30.0,
        40.0,
    ]
    # Compare normalized datetime values because SQLite drops timezone metadata
    # while PostgreSQL preserves it.
    assert parse_api_datetime(payload["window_started_at"]) == datetime(
        2026,
        9,
        16,
        18,
        2,
        tzinfo=UTC,
    )
    assert parse_api_datetime(payload["window_ended_at"]) == datetime(
        2026,
        9,
        16,
        18,
        3,
        tzinfo=UTC,
    )


async def test_metric_summary_returns_not_found(
    api_client: AsyncClient,
) -> None:
    """Return HTTP 404 when no samples match the metric name."""

    # Arrange: seed telemetry that does not contain the requested metric.
    await seed_dashboard_metrics(api_client)
    params = dashboard_params()
    params["metric"] = "missing_metric"

    # Act: request a metric absent from the bounded service window.
    response = await api_client.get(
        "/api/v1/dashboard/metrics/summary",
        params=params,
    )
    payload = response.json()

    # Assert: the API reports the missing metric clearly.
    assert response.status_code == 404
    assert "No samples found for metric 'missing_metric'" in payload["detail"]


async def test_metric_summary_rejects_inconsistent_units(
    api_client: AsyncClient,
) -> None:
    """Reject aggregation when one metric name uses different units."""

    # Arrange: register the service and create samples whose shared name has
    # incompatible units.
    await register_dashboard_service(api_client)

    ingest_response = await api_client.post(
        "/api/v1/telemetry",
        json={
            "items": [
                metric_item(
                    value=50.0,
                    timestamp="2026-09-16T18:00:00Z",
                    unit="milliseconds",
                ),
                metric_item(
                    value=0.05,
                    timestamp="2026-09-16T18:01:00Z",
                    unit="seconds",
                ),
            ]
        },
    )
    assert ingest_response.status_code == 202

    # Act: attempt to combine incompatible measurements.
    response = await api_client.get(
        "/api/v1/dashboard/metrics/summary",
        params=dashboard_params(),
    )
    payload = response.json()

    # Assert: invalid aggregation maps to HTTP 422.
    assert response.status_code == 422
    assert "contains inconsistent units" in payload["detail"]


async def test_metric_summary_rejects_reversed_time_window(
    api_client: AsyncClient,
) -> None:
    """Reject a dashboard query whose start occurs after its end."""

    # Arrange: registration is sufficient because validation occurs before the
    # repository query.
    await register_dashboard_service(api_client)
    params = dashboard_params()
    params["observed_from"] = "2026-09-16T18:05:00Z"
    params["observed_to"] = "2026-09-16T18:00:00Z"

    # Act: submit the reversed time interval.
    response = await api_client.get(
        "/api/v1/dashboard/metrics/summary",
        params=params,
    )
    payload = response.json()

    # Assert: domain time-window validation maps to HTTP 422.
    assert response.status_code == 422
    assert (
        payload["detail"]
        == "observed_from must be earlier than or equal to observed_to"
    )
