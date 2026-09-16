from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from observability_platform.schemas.anomaly import (
    AnomalyCategory,
    AnomalySeverity,
)
from observability_platform.schemas.correlation import RootCauseCandidate


@dataclass(frozen=True)
class CorrelationSignal:
    anomaly_id: UUID
    incident_id: UUID
    rule_id: str
    category: AnomalyCategory
    severity: AnomalySeverity
    source: str
    observed_at: datetime


class RootCauseAnalysisEngine:
    def analyze(
        self,
        signals: list[CorrelationSignal],
    ) -> RootCauseCandidate:
        if not signals:
            raise ValueError("At least one correlation signal is required")

        earliest_observed_at = min(signal.observed_at for signal in signals)
        source_counts = Counter(signal.source for signal in signals)

        candidates = [
            self._score_signal(
                signal,
                earliest_observed_at=earliest_observed_at,
                source_count=source_counts[signal.source],
            )
            for signal in signals
        ]

        return min(
            candidates,
            key=lambda candidate: (
                -candidate.confidence_score,
                candidate.observed_at,
                str(candidate.anomaly_id),
            ),
        )

    def _score_signal(
        self,
        signal: CorrelationSignal,
        *,
        earliest_observed_at: datetime,
        source_count: int,
    ) -> RootCauseCandidate:
        score = 0.25
        reasons = ["Signal is part of the correlated incident window"]

        if signal.observed_at == earliest_observed_at:
            score += 0.25
            reasons.append("Signal is the earliest observed anomaly")

        category_scores = {
            AnomalyCategory.EVENT_SEVERITY: 0.20,
            AnomalyCategory.LOG_SEVERITY: 0.10,
            AnomalyCategory.METRIC_THRESHOLD: 0.05,
        }
        score += category_scores[signal.category]
        reasons.append(f"Category '{signal.category.value}' contributes causal weight")

        if signal.severity is AnomalySeverity.CRITICAL:
            score += 0.15
            reasons.append("Signal severity is critical")
        else:
            score += 0.05
            reasons.append("Signal severity is warning")

        if source_count > 1:
            score += 0.15
            reasons.append(f"Source appears in {source_count} correlated incidents")

        return RootCauseCandidate(
            anomaly_id=signal.anomaly_id,
            incident_id=signal.incident_id,
            rule_id=signal.rule_id,
            category=signal.category,
            severity=signal.severity,
            source=signal.source,
            observed_at=signal.observed_at,
            confidence_score=round(min(score, 1.0), 2),
            reasons=reasons,
        )
