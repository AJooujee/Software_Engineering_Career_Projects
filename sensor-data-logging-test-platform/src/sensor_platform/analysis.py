"""Fault detection and health analysis for sensor readings."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace

from sensor_platform.models import SensorReading, SensorStatus, SensorType


@dataclass(frozen=True, slots=True)
class SensorThreshold:
    """Normal and critical operating boundaries for one sensor type."""

    critical_minimum: float
    normal_minimum: float
    normal_maximum: float
    critical_maximum: float

    def __post_init__(self) -> None:
        """Reject threshold boundaries that are incorrectly ordered."""

        boundaries = (
            self.critical_minimum,
            self.normal_minimum,
            self.normal_maximum,
            self.critical_maximum,
        )

        if boundaries != tuple(sorted(boundaries)):
            raise ValueError(
                "Thresholds must be ordered from critical minimum "
                "to critical maximum"
            )


# Default hardware operating ranges used by the analysis engine.
DEFAULT_THRESHOLDS: dict[SensorType, SensorThreshold] = {
    SensorType.TEMPERATURE: SensorThreshold(15.0, 20.0, 30.0, 35.0),
    SensorType.VOLTAGE: SensorThreshold(10.5, 11.5, 12.5, 13.5),
    SensorType.CURRENT: SensorThreshold(0.1, 0.5, 5.0, 7.0),
    SensorType.VIBRATION: SensorThreshold(0.0, 0.0, 4.0, 7.0),
}


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    """Result produced after evaluating one sensor reading."""

    reading: SensorReading
    reason: str
    deviation_from_normal: float


@dataclass(frozen=True, slots=True)
class HealthSummary:
    """Aggregated health information for a collection of readings."""

    total_readings: int
    normal_count: int
    warning_count: int
    fault_count: int
    health_score: float


class FaultDetector:
    """Classify sensor readings using configurable operating thresholds."""

    def __init__(
        self,
        thresholds: Mapping[SensorType, SensorThreshold] | None = None,
    ) -> None:
        # Copy the configuration so outside changes cannot affect this object.
        self._thresholds = dict(thresholds or DEFAULT_THRESHOLDS)

    def analyze(self, reading: SensorReading) -> AnalysisResult:
        """Classify one reading as normal, warning, or fault."""

        threshold = self._thresholds[reading.sensor_type]
        value = reading.value

        if threshold.normal_minimum <= value <= threshold.normal_maximum:
            status = SensorStatus.NORMAL
            reason = "Value is within the normal operating range."
            deviation = 0.0

        elif threshold.critical_minimum <= value <= threshold.critical_maximum:
            status = SensorStatus.WARNING
            direction = (
                "below"
                if value < threshold.normal_minimum
                else "above"
            )
            reason = f"Value is {direction} the normal operating range."
            deviation = self._deviation_from_normal(value, threshold)

        else:
            status = SensorStatus.FAULT
            direction = (
                "below"
                if value < threshold.critical_minimum
                else "above"
            )
            reason = f"Value is {direction} the critical safety limit."
            deviation = self._deviation_from_normal(value, threshold)

        # Preserve the original immutable reading while updating its status.
        analyzed_reading = replace(reading, status=status)

        return AnalysisResult(
            reading=analyzed_reading,
            reason=reason,
            deviation_from_normal=deviation,
        )

    def analyze_many(
        self,
        readings: Iterable[SensorReading],
    ) -> list[AnalysisResult]:
        """Analyze multiple readings using the same detector."""

        return [self.analyze(reading) for reading in readings]

    def summarize(
        self,
        results: Iterable[AnalysisResult],
    ) -> HealthSummary:
        """Calculate status counts and an overall health score."""

        result_list = list(results)
        total = len(result_list)

        normal_count = sum(
            result.reading.status == SensorStatus.NORMAL
            for result in result_list
        )
        warning_count = sum(
            result.reading.status == SensorStatus.WARNING
            for result in result_list
        )
        fault_count = sum(
            result.reading.status == SensorStatus.FAULT
            for result in result_list
        )

        # Normal readings receive full credit and warnings receive half.
        health_score = (
            round(
                ((normal_count + warning_count * 0.5) / total) * 100,
                2,
            )
            if total
            else 0.0
        )

        return HealthSummary(
            total_readings=total,
            normal_count=normal_count,
            warning_count=warning_count,
            fault_count=fault_count,
            health_score=health_score,
        )

    @staticmethod
    def _deviation_from_normal(
        value: float,
        threshold: SensorThreshold,
    ) -> float:
        """Measure how far a value is outside its normal range."""

        if value < threshold.normal_minimum:
            boundary = threshold.normal_minimum
        else:
            boundary = threshold.normal_maximum

        return round(abs(value - boundary), 3)
