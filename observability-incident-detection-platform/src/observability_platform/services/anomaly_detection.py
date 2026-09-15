from dataclasses import dataclass

from observability_platform.schemas.anomaly import (
    AnomalyCategory,
    AnomalyFinding,
    AnomalySeverity,
)
from observability_platform.schemas.telemetry import (
    EventSeverity,
    EventTelemetry,
    LogLevel,
    LogTelemetry,
    MetricTelemetry,
    TelemetryItem,
)


@dataclass(frozen=True)
class MetricThresholdRule:
    rule_id: str
    metric_name: str
    threshold: float
    unit: str
    severity: AnomalySeverity
    title: str


METRIC_RULES = (
    MetricThresholdRule(
        rule_id="metric.cpu_usage.high",
        metric_name="cpu_usage",
        threshold=90.0,
        unit="percent",
        severity=AnomalySeverity.CRITICAL,
        title="High CPU usage",
    ),
    MetricThresholdRule(
        rule_id="metric.memory_usage.high",
        metric_name="memory_usage",
        threshold=90.0,
        unit="percent",
        severity=AnomalySeverity.CRITICAL,
        title="High memory usage",
    ),
    MetricThresholdRule(
        rule_id="metric.response_latency.high",
        metric_name="response_latency",
        threshold=500.0,
        unit="milliseconds",
        severity=AnomalySeverity.WARNING,
        title="High response latency",
    ),
    MetricThresholdRule(
        rule_id="metric.error_rate.high",
        metric_name="error_rate",
        threshold=5.0,
        unit="percent",
        severity=AnomalySeverity.CRITICAL,
        title="High error rate",
    ),
)


class AnomalyDetectionEngine:
    def evaluate(self, item: TelemetryItem) -> list[AnomalyFinding]:
        if isinstance(item, MetricTelemetry):
            return self._evaluate_metric(item)
        if isinstance(item, LogTelemetry):
            return self._evaluate_log(item)
        if isinstance(item, EventTelemetry):
            return self._evaluate_event(item)

        return []

    def _evaluate_metric(
        self,
        item: MetricTelemetry,
    ) -> list[AnomalyFinding]:
        findings = []

        for rule in METRIC_RULES:
            if (
                item.name == rule.metric_name
                and item.unit == rule.unit
                and item.value >= rule.threshold
            ):
                findings.append(
                    AnomalyFinding(
                        rule_id=rule.rule_id,
                        category=AnomalyCategory.METRIC_THRESHOLD,
                        severity=rule.severity,
                        title=rule.title,
                        description=(
                            f"{item.name} reached {item.value} {rule.unit}; "
                            f"threshold is {rule.threshold} {rule.unit}"
                        ),
                        service=item.service,
                        environment=item.environment,
                        source=item.source,
                        observed_at=item.timestamp,
                        observed_value=item.value,
                        threshold=rule.threshold,
                    )
                )

        return findings

    def _evaluate_log(
        self,
        item: LogTelemetry,
    ) -> list[AnomalyFinding]:
        severity_map = {
            LogLevel.ERROR: AnomalySeverity.WARNING,
            LogLevel.CRITICAL: AnomalySeverity.CRITICAL,
        }
        severity = severity_map.get(item.level)

        if severity is None:
            return []

        return [
            AnomalyFinding(
                rule_id=f"log.level.{item.level.value}",
                category=AnomalyCategory.LOG_SEVERITY,
                severity=severity,
                title=f"{item.level.value.title()} log detected",
                description=item.message,
                service=item.service,
                environment=item.environment,
                source=item.source,
                observed_at=item.timestamp,
                observed_value=item.level.value,
                threshold=LogLevel.ERROR.value,
            )
        ]

    def _evaluate_event(
        self,
        item: EventTelemetry,
    ) -> list[AnomalyFinding]:
        severity_map = {
            EventSeverity.ERROR: AnomalySeverity.WARNING,
            EventSeverity.CRITICAL: AnomalySeverity.CRITICAL,
        }
        severity = severity_map.get(item.severity)

        if severity is None:
            return []

        return [
            AnomalyFinding(
                rule_id=f"event.severity.{item.severity.value}",
                category=AnomalyCategory.EVENT_SEVERITY,
                severity=severity,
                title=f"{item.severity.value.title()} event detected",
                description=item.description or item.name,
                service=item.service,
                environment=item.environment,
                source=item.source,
                observed_at=item.timestamp,
                observed_value=item.severity.value,
                threshold=EventSeverity.ERROR.value,
            )
        ]
