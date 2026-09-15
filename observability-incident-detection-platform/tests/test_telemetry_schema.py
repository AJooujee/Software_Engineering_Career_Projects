import pytest
from pydantic import ValidationError

from observability_platform.schemas.telemetry import (
    EventTelemetry,
    LogTelemetry,
    MetricTelemetry,
    TelemetryBatch,
)


def test_metric_telemetry_accepts_valid_data() -> None:
    metric = MetricTelemetry(
        service="checkout-service",
        source="checkout-instance-1",
        name="cpu_usage",
        value=72.5,
        unit="percent",
    )

    assert metric.type == "metric"
    assert metric.value == 72.5
    assert metric.timestamp.tzinfo is not None


def test_batch_accepts_mixed_telemetry_types() -> None:
    batch = TelemetryBatch(
        items=[
            {
                "type": "metric",
                "service": "checkout-service",
                "source": "checkout-instance-1",
                "name": "request_latency",
                "value": 145.2,
                "unit": "milliseconds",
            },
            {
                "type": "log",
                "service": "checkout-service",
                "source": "checkout-instance-1",
                "level": "error",
                "message": "Payment provider timed out",
            },
            {
                "type": "event",
                "service": "checkout-service",
                "source": "checkout-instance-1",
                "name": "service_restart",
                "severity": "warning",
                "description": "Instance restarted after a failed health check",
            },
        ]
    )

    assert len(batch.items) == 3
    assert isinstance(batch.items[0], MetricTelemetry)
    assert isinstance(batch.items[1], LogTelemetry)
    assert isinstance(batch.items[2], EventTelemetry)


def test_batch_rejects_empty_items() -> None:
    with pytest.raises(ValidationError):
        TelemetryBatch(items=[])


def test_batch_rejects_unknown_telemetry_type() -> None:
    with pytest.raises(ValidationError):
        TelemetryBatch(
            items=[
                {
                    "type": "trace",
                    "service": "checkout-service",
                    "source": "checkout-instance-1",
                }
            ]
        )


def test_metric_rejects_infinite_value() -> None:
    with pytest.raises(ValidationError):
        MetricTelemetry(
            service="checkout-service",
            source="checkout-instance-1",
            name="cpu_usage",
            value=float("inf"),
        )


def test_telemetry_rejects_unexpected_fields() -> None:
    with pytest.raises(ValidationError):
        LogTelemetry(
            service="checkout-service",
            source="checkout-instance-1",
            level="info",
            message="Service started",
            unexpected_field="not-allowed",
        )
