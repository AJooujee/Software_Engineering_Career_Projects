"""Unit tests for distributed tracing request schema validation."""

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from observability_platform.schemas.trace import (
    TraceBatchCreate,
    TraceSpanCreate,
)


def valid_span_data() -> dict:
    """Build one valid span payload that individual tests can modify."""

    # Use a fixed timezone-aware timestamp so test results remain deterministic.
    started_at = datetime(2026, 9, 16, 18, 0, tzinfo=UTC)

    # This payload satisfies identifier, timing, service, and operation rules.
    return {
        "trace_id": "a" * 32,
        "span_id": "b" * 16,
        "parent_span_id": None,
        "service": "payment-service",
        "environment": "production",
        "source": "payment-instance-1",
        "operation": "POST /payments",
        "status": "ok",
        "started_at": started_at,
        "ended_at": started_at + timedelta(milliseconds=125),
        "attributes": {
            "http.method": "POST",
            "http.status_code": 200,
        },
    }


def test_trace_span_accepts_valid_w3c_identifiers() -> None:
    """Accept lowercase W3C trace and span identifiers of valid lengths."""

    # Arrange: create a complete valid span payload.
    data = valid_span_data()

    # Act: validate and convert the dictionary into a Pydantic model.
    span = TraceSpanCreate.model_validate(data)

    # Assert: identifiers and enum values survive schema conversion.
    assert span.trace_id == "a" * 32
    assert span.span_id == "b" * 16
    assert span.parent_span_id is None
    assert span.status.value == "ok"


def test_trace_span_rejects_invalid_trace_id() -> None:
    """Reject a trace identifier that does not follow the W3C format."""

    # Arrange: replace the valid hexadecimal identifier with invalid text.
    data = valid_span_data()
    data["trace_id"] = "not-a-w3c-trace-id"

    # Act and assert: field validation must reject the malformed identifier.
    with pytest.raises(ValidationError):
        TraceSpanCreate.model_validate(data)


def test_trace_span_rejects_end_before_start() -> None:
    """Reject spans whose ending timestamp precedes their start."""

    # Arrange: create an impossible negative-duration time interval.
    data = valid_span_data()
    data["ended_at"] = data["started_at"] - timedelta(milliseconds=1)

    # Act and assert: cross-field validation must report the timing rule.
    with pytest.raises(
        ValidationError,
        match="ended_at must be greater than or equal to started_at",
    ):
        TraceSpanCreate.model_validate(data)


def test_trace_span_rejects_self_parent() -> None:
    """Reject a span that identifies itself as its own parent."""

    # Arrange: create an immediate cycle in the trace graph.
    data = valid_span_data()
    data["parent_span_id"] = data["span_id"]

    # Act and assert: graph identity validation must reject self-parenting.
    with pytest.raises(
        ValidationError,
        match="parent_span_id must differ from span_id",
    ):
        TraceSpanCreate.model_validate(data)


def test_trace_batch_requires_at_least_one_span() -> None:
    """Reject an ingestion batch that contains no trace spans."""

    # Arrange: construct an empty batch payload.
    data = {"spans": []}

    # Act and assert: a trace ingestion request must contain at least one span.
    with pytest.raises(ValidationError):
        TraceBatchCreate.model_validate(data)
