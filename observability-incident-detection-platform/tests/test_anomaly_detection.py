import pytest

from observability_platform.schemas.telemetry import (
    EventTelemetry,
    LogTelemetry,
    MetricTelemetry,
)
from observability_platform.services.anomaly_detection import (
    AnomalyDetectionEngine,
)


@pytest.fixture
def engine() -> AnomalyDetectionEngine:
    return AnomalyDetectionEngine()


@pytest.mark.parametrize(
    ("name", "value", "unit", "expected_rule", "expected_severity"),
    [
        (
            "cpu_usage",
            90.0,
            "percent",
            "metric.cpu_usage.high",
            "critical",
        ),
        (
            "memory_usage",
            95.0,
            "percent",
            "metric.memory_usage.high",
            "critical",
        ),
        (
            "response_latency",
            500.0,
            "milliseconds",
            "metric.response_latency.high",
            "warning",
        ),
        (
            "error_rate",
            7.5,
            "percent",
            "metric.error_rate.high",
            "critical",
        ),
    ],
)
def test_metric_threshold_creates_finding(
    engine: AnomalyDetectionEngine,
    name: str,
    value: float,
    unit: str,
    expected_rule: str,
    expected_severity: str,
) -> None:
    item = MetricTelemetry(
        service="payment-service",
        source="payment-instance-1",
        name=name,
        value=value,
        unit=unit,
    )

    findings = engine.evaluate(item)

    assert len(findings) == 1
    assert findings[0].rule_id == expected_rule
    assert findings[0].severity.value == expected_severity
    assert findings[0].observed_value == value


def test_metric_below_threshold_is_not_anomaly(
    engine: AnomalyDetectionEngine,
) -> None:
    item = MetricTelemetry(
        service="payment-service",
        source="payment-instance-1",
        name="cpu_usage",
        value=45.0,
        unit="percent",
    )

    assert engine.evaluate(item) == []


def test_metric_with_unexpected_unit_is_not_evaluated(
    engine: AnomalyDetectionEngine,
) -> None:
    item = MetricTelemetry(
        service="payment-service",
        source="payment-instance-1",
        name="response_latency",
        value=900.0,
        unit="seconds",
    )

    assert engine.evaluate(item) == []


@pytest.mark.parametrize(
    ("level", "expected_severity"),
    [
        ("error", "warning"),
        ("critical", "critical"),
    ],
)
def test_error_log_creates_finding(
    engine: AnomalyDetectionEngine,
    level: str,
    expected_severity: str,
) -> None:
    item = LogTelemetry(
        service="payment-service",
        source="payment-instance-1",
        level=level,
        message="Request processing failed",
    )

    findings = engine.evaluate(item)

    assert len(findings) == 1
    assert findings[0].rule_id == f"log.level.{level}"
    assert findings[0].severity.value == expected_severity


def test_info_log_is_not_anomaly(
    engine: AnomalyDetectionEngine,
) -> None:
    item = LogTelemetry(
        service="payment-service",
        source="payment-instance-1",
        level="info",
        message="Request completed",
    )

    assert engine.evaluate(item) == []


@pytest.mark.parametrize(
    ("severity", "expected_severity"),
    [
        ("error", "warning"),
        ("critical", "critical"),
    ],
)
def test_error_event_creates_finding(
    engine: AnomalyDetectionEngine,
    severity: str,
    expected_severity: str,
) -> None:
    item = EventTelemetry(
        service="payment-service",
        source="payment-instance-1",
        name="provider_failure",
        severity=severity,
        description="Payment provider became unavailable",
    )

    findings = engine.evaluate(item)

    assert len(findings) == 1
    assert findings[0].rule_id == f"event.severity.{severity}"
    assert findings[0].severity.value == expected_severity


def test_warning_event_is_not_anomaly(
    engine: AnomalyDetectionEngine,
) -> None:
    item = EventTelemetry(
        service="payment-service",
        source="payment-instance-1",
        name="deployment_started",
        severity="warning",
    )

    assert engine.evaluate(item) == []
