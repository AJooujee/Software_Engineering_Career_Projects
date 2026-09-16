from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from observability_platform.schemas.anomaly import (
    AnomalyCategory,
    AnomalySeverity,
)
from observability_platform.services.root_cause_analysis import (
    CorrelationSignal,
    RootCauseAnalysisEngine,
)


def make_signal(
    *,
    category: AnomalyCategory,
    severity: AnomalySeverity,
    source: str,
    observed_at: datetime,
) -> CorrelationSignal:
    return CorrelationSignal(
        anomaly_id=uuid4(),
        incident_id=uuid4(),
        rule_id=f"test.{category.value}",
        category=category,
        severity=severity,
        source=source,
        observed_at=observed_at,
    )


def test_analyze_rejects_empty_signals() -> None:
    engine = RootCauseAnalysisEngine()

    with pytest.raises(
        ValueError,
        match="At least one correlation signal is required",
    ):
        engine.analyze([])


def test_earliest_critical_event_is_selected() -> None:
    engine = RootCauseAnalysisEngine()
    started_at = datetime(2026, 9, 16, 10, 0, tzinfo=UTC)

    earliest_event = make_signal(
        category=AnomalyCategory.EVENT_SEVERITY,
        severity=AnomalySeverity.CRITICAL,
        source="checkout-instance-1",
        observed_at=started_at,
    )
    later_metric = make_signal(
        category=AnomalyCategory.METRIC_THRESHOLD,
        severity=AnomalySeverity.CRITICAL,
        source="checkout-instance-2",
        observed_at=started_at + timedelta(minutes=2),
    )

    candidate = engine.analyze([later_metric, earliest_event])

    assert candidate.anomaly_id == earliest_event.anomaly_id
    assert candidate.incident_id == earliest_event.incident_id
    assert candidate.confidence_score == 0.85
    assert "Signal is the earliest observed anomaly" in candidate.reasons


def test_repeated_source_increases_and_caps_confidence() -> None:
    engine = RootCauseAnalysisEngine()
    started_at = datetime(2026, 9, 16, 10, 0, tzinfo=UTC)

    earliest_event = make_signal(
        category=AnomalyCategory.EVENT_SEVERITY,
        severity=AnomalySeverity.CRITICAL,
        source="shared-instance",
        observed_at=started_at,
    )
    related_log = make_signal(
        category=AnomalyCategory.LOG_SEVERITY,
        severity=AnomalySeverity.CRITICAL,
        source="shared-instance",
        observed_at=started_at + timedelta(minutes=1),
    )

    candidate = engine.analyze([earliest_event, related_log])

    assert candidate.anomaly_id == earliest_event.anomaly_id
    assert candidate.confidence_score == 1.0
    assert "Source appears in 2 correlated incidents" in candidate.reasons


def test_equal_scores_use_earliest_signal_as_tiebreaker() -> None:
    engine = RootCauseAnalysisEngine()
    started_at = datetime(2026, 9, 16, 10, 0, tzinfo=UTC)

    earliest_metric = make_signal(
        category=AnomalyCategory.METRIC_THRESHOLD,
        severity=AnomalySeverity.WARNING,
        source="metric-instance",
        observed_at=started_at,
    )
    later_event = make_signal(
        category=AnomalyCategory.EVENT_SEVERITY,
        severity=AnomalySeverity.CRITICAL,
        source="event-instance",
        observed_at=started_at + timedelta(minutes=1),
    )

    candidate = engine.analyze([later_event, earliest_metric])

    assert candidate.anomaly_id == earliest_metric.anomaly_id
    assert candidate.confidence_score == 0.60
