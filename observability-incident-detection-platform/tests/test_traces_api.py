"""Integration tests for distributed tracing ingestion and retrieval APIs."""

import pytest
from httpx2 import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from observability_platform.db.models import TraceSpanRecord

# Every test in this module uses async FastAPI and database operations.
pytestmark = pytest.mark.asyncio

# Use valid W3C-style hexadecimal identifiers throughout the test suite.
TRACE_ID = "a" * 32
ROOT_SPAN_ID = "b" * 16
CHILD_SPAN_ID = "c" * 16


async def register_trace_services(api_client: AsyncClient) -> None:
    """Register every monitored service referenced by the sample trace."""

    # A distributed trace may cross multiple independently monitored services.
    for name in ("gateway-service", "payment-service"):
        response = await api_client.post(
            "/api/v1/services",
            json={
                "name": name,
                "environment": "production",
            },
        )

        # Service registration is a prerequisite for trace ingestion.
        assert response.status_code == 201


def trace_payload(
    *,
    trace_id: str = TRACE_ID,
) -> dict:
    """Build a valid two-span trace shared by multiple API tests."""

    # The gateway span is the root operation and covers the complete request.
    root_span = {
        "trace_id": trace_id,
        "span_id": ROOT_SPAN_ID,
        "parent_span_id": None,
        "service": "gateway-service",
        "environment": "production",
        "source": "gateway-instance-1",
        "operation": "POST /checkout",
        "status": "ok",
        "started_at": "2026-09-16T18:00:00Z",
        "ended_at": "2026-09-16T18:00:00.150Z",
        "attributes": {
            "http.method": "POST",
            "http.status_code": 200,
        },
    }

    # The payment span represents a downstream operation inside the root span.
    child_span = {
        "trace_id": trace_id,
        "span_id": CHILD_SPAN_ID,
        "parent_span_id": ROOT_SPAN_ID,
        "service": "payment-service",
        "environment": "production",
        "source": "payment-instance-1",
        "operation": "authorize_payment",
        "status": "ok",
        "started_at": "2026-09-16T18:00:00.025Z",
        "ended_at": "2026-09-16T18:00:00.100Z",
        "attributes": {
            "payment.provider": "sandbox",
        },
    }

    # Both spans share one trace ID and should be stored atomically.
    return {
        "spans": [
            root_span,
            child_span,
        ]
    }


async def test_ingest_and_get_distributed_trace(
    api_client: AsyncClient,
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Persist and reconstruct a valid multi-service distributed trace."""

    # Arrange: register all services referenced by the sample trace.
    await register_trace_services(api_client)

    # Act: ingest the root and child spans in one request.
    ingest_response = await api_client.post(
        "/api/v1/traces",
        json=trace_payload(),
    )
    ingest_payload = ingest_response.json()

    # Assert: both spans were accepted and received persistent UUIDs.
    assert ingest_response.status_code == 202
    assert ingest_payload["accepted_count"] == 2
    assert len(ingest_payload["span_record_ids"]) == 2
    assert ingest_payload["received_at"] is not None

    # Act: retrieve the complete trace using its W3C trace identifier.
    response = await api_client.get(f"/api/v1/traces/{TRACE_ID}")
    payload = response.json()

    # Assert: the response represents the requested trace.
    assert response.status_code == 200
    assert payload["trace_id"] == TRACE_ID
    assert payload["span_count"] == 2

    # The trace duration uses the complete wall-clock interval from the
    # earliest start to the latest end, not the sum of overlapping spans.
    assert payload["duration_ms"] == 150.0

    # Service names are deduplicated and returned in deterministic order.
    assert payload["services"] == [
        "gateway-service",
        "payment-service",
    ]

    # Spans are ordered chronologically by the repository.
    assert [span["span_id"] for span in payload["spans"]] == [
        ROOT_SPAN_ID,
        CHILD_SPAN_ID,
    ]

    # Verify individual duration calculations for the root and child spans.
    assert payload["spans"][0]["duration_ms"] == 150.0
    assert payload["spans"][1]["duration_ms"] == 75.0

    # Verify that the child-to-parent relationship survives persistence.
    assert payload["spans"][0]["parent_span_id"] is None
    assert payload["spans"][1]["parent_span_id"] == ROOT_SPAN_ID

    # Verify that each span retains its originating service identity.
    assert payload["spans"][0]["service"] == "gateway-service"
    assert payload["spans"][1]["service"] == "payment-service"

    # Assert directly against the database so the test verifies persistence,
    # rather than validating only the HTTP response.
    async with test_session_factory() as session:
        result = await session.execute(
            select(func.count()).select_from(TraceSpanRecord)
        )

    assert result.scalar_one() == 2


async def test_ingest_rejects_mixed_trace_ids(
    api_client: AsyncClient,
) -> None:
    """Reject a batch containing spans from different distributed traces."""

    # Arrange: register services and begin with a valid trace payload.
    await register_trace_services(api_client)
    payload = trace_payload()

    # Change the child span to a different trace ID. One ingestion transaction
    # cannot represent multiple independent distributed traces.
    payload["spans"][1]["trace_id"] = "d" * 32

    # Act: submit the invalid mixed-trace batch.
    response = await api_client.post(
        "/api/v1/traces",
        json=payload,
    )
    response_payload = response.json()

    # Assert: the domain validation maps to an HTTP 422 response.
    assert response.status_code == 422
    assert (
        response_payload["detail"]
        == "All spans in a batch must share the same trace_id"
    )


async def test_ingest_rejects_duplicate_span_ids_in_batch(
    api_client: AsyncClient,
) -> None:
    """Reject duplicate span identities inside one ingestion request."""

    # Arrange: register services and create a valid two-span trace.
    await register_trace_services(api_client)
    payload = trace_payload()

    # Reuse the root span ID for the child. The parent is cleared so schema
    # validation does not reject self-parenting before duplicate detection.
    payload["spans"][1]["span_id"] = ROOT_SPAN_ID
    payload["spans"][1]["parent_span_id"] = None

    # Act: submit the batch containing duplicate span IDs.
    response = await api_client.post(
        "/api/v1/traces",
        json=payload,
    )
    response_payload = response.json()

    # Assert: duplicate identities conflict with the trace resource.
    assert response.status_code == 409
    assert "contains duplicate span_ids" in response_payload["detail"]


async def test_ingest_rejects_existing_span_ids(
    api_client: AsyncClient,
) -> None:
    """Reject replaying spans already stored for the same trace."""

    # Arrange: register services and persist the sample trace once.
    await register_trace_services(api_client)

    first_response = await api_client.post(
        "/api/v1/traces",
        json=trace_payload(),
    )
    assert first_response.status_code == 202

    # Act: replay the exact same trace batch.
    second_response = await api_client.post(
        "/api/v1/traces",
        json=trace_payload(),
    )
    second_payload = second_response.json()

    # Assert: the repository detects existing trace/span identity pairs.
    assert second_response.status_code == 409
    assert "already contains span_ids" in second_payload["detail"]


async def test_ingest_rejects_unregistered_service(
    api_client: AsyncClient,
) -> None:
    """Reject spans emitted by a service absent from the registry."""

    # Arrange: use only the root span without registering its service.
    payload = trace_payload()
    payload["spans"] = [payload["spans"][0]]

    # Act: attempt to ingest the trace span.
    response = await api_client.post(
        "/api/v1/traces",
        json=payload,
    )
    response_payload = response.json()

    # Assert: service registry validation maps to HTTP 422.
    assert response.status_code == 422
    assert "is not registered" in response_payload["detail"]


async def test_get_trace_returns_not_found(
    api_client: AsyncClient,
) -> None:
    """Return HTTP 404 when a valid trace ID has no stored spans."""

    # Arrange: use a valid W3C identifier that is absent from the database.
    missing_trace_id = "f" * 32

    # Act: request the nonexistent trace.
    response = await api_client.get(f"/api/v1/traces/{missing_trace_id}")
    response_payload = response.json()

    # Assert: the error identifies the missing trace.
    assert response.status_code == 404
    assert missing_trace_id in response_payload["detail"]
