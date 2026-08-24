"""Automated pass/fail testing for simulated hardware sensors."""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum

from sensor_platform.analysis import FaultDetector
from sensor_platform.models import SensorReading, SensorType


class HardwareTestOutcome(str, Enum):
    """Final outcome assigned to a hardware test."""

    PASS = "pass"
    FAIL = "fail"


@dataclass(frozen=True, slots=True)
class HardwareTestCriteria:
    """Acceptance criteria applied to every tested sensor."""

    minimum_readings: int = 5
    maximum_fault_count: int = 0
    maximum_warning_rate: float = 0.20
    minimum_health_score: float = 80.0

    def __post_init__(self) -> None:
        """Reject test criteria containing invalid values."""

        if self.minimum_readings <= 0:
            raise ValueError("minimum_readings must be greater than zero")

        if self.maximum_fault_count < 0:
            raise ValueError("maximum_fault_count cannot be negative")

        if not 0 <= self.maximum_warning_rate <= 1:
            raise ValueError(
                "maximum_warning_rate must be between 0 and 1"
            )

        if not 0 <= self.minimum_health_score <= 100:
            raise ValueError(
                "minimum_health_score must be between 0 and 100"
            )


@dataclass(frozen=True, slots=True)
class HardwareTestResult:
    """Pass/fail result for one physical or simulated sensor."""

    sensor_id: str
    sensor_type: SensorType
    outcome: HardwareTestOutcome
    total_readings: int
    normal_count: int
    warning_count: int
    fault_count: int
    warning_rate: float
    health_score: float
    failure_reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        """Convert the result into a JSON-compatible dictionary."""

        return {
            "sensor_id": self.sensor_id,
            "sensor_type": self.sensor_type.value,
            "outcome": self.outcome.value,
            "total_readings": self.total_readings,
            "normal_count": self.normal_count,
            "warning_count": self.warning_count,
            "fault_count": self.fault_count,
            "warning_rate": self.warning_rate,
            "health_score": self.health_score,
            "failure_reasons": list(self.failure_reasons),
        }


@dataclass(frozen=True, slots=True)
class HardwareTestReport:
    """Combined result for all sensors included in one test run."""

    overall_outcome: HardwareTestOutcome
    total_sensors: int
    passed_sensors: int
    failed_sensors: int
    results: tuple[HardwareTestResult, ...]

    def to_dict(self) -> dict[str, object]:
        """Convert the complete report into JSON-compatible data."""

        return {
            "overall_outcome": self.overall_outcome.value,
            "total_sensors": self.total_sensors,
            "passed_sensors": self.passed_sensors,
            "failed_sensors": self.failed_sensors,
            "results": [result.to_dict() for result in self.results],
        }


class HardwareTestRunner:
    """Analyze readings and evaluate configurable pass/fail criteria."""

    def __init__(
        self,
        detector: FaultDetector | None = None,
        criteria: HardwareTestCriteria | None = None,
    ) -> None:
        self._detector = detector or FaultDetector()
        self._criteria = criteria or HardwareTestCriteria()

    def run(
        self,
        readings: Iterable[SensorReading],
    ) -> HardwareTestReport:
        """Group readings by sensor and execute the automated tests."""

        reading_list = list(readings)

        if not reading_list:
            raise ValueError("At least one sensor reading is required")

        grouped_readings: dict[
            tuple[str, SensorType],
            list[SensorReading],
        ] = defaultdict(list)

        # Sensor ID and type together uniquely identify the tested device.
        for reading in reading_list:
            key = (reading.sensor_id, reading.sensor_type)
            grouped_readings[key].append(reading)

        results = tuple(
            self._evaluate_sensor(sensor_id, sensor_type, sensor_readings)
            for (sensor_id, sensor_type), sensor_readings
            in sorted(
                grouped_readings.items(),
                key=lambda item: (item[0][1].value, item[0][0]),
            )
        )

        passed_sensors = sum(
            result.outcome == HardwareTestOutcome.PASS
            for result in results
        )
        failed_sensors = len(results) - passed_sensors

        overall_outcome = (
            HardwareTestOutcome.PASS
            if failed_sensors == 0
            else HardwareTestOutcome.FAIL
        )

        return HardwareTestReport(
            overall_outcome=overall_outcome,
            total_sensors=len(results),
            passed_sensors=passed_sensors,
            failed_sensors=failed_sensors,
            results=results,
        )

    def _evaluate_sensor(
        self,
        sensor_id: str,
        sensor_type: SensorType,
        readings: list[SensorReading],
    ) -> HardwareTestResult:
        """Apply all acceptance criteria to one sensor."""

        analysis_results = self._detector.analyze_many(readings)
        summary = self._detector.summarize(analysis_results)

        warning_rate = summary.warning_count / summary.total_readings
        failure_reasons: list[str] = []

        if summary.total_readings < self._criteria.minimum_readings:
            failure_reasons.append(
                "Insufficient readings: "
                f"expected at least {self._criteria.minimum_readings}"
            )

        if summary.fault_count > self._criteria.maximum_fault_count:
            failure_reasons.append(
                f"Fault count {summary.fault_count} exceeds "
                f"maximum {self._criteria.maximum_fault_count}"
            )

        if warning_rate > self._criteria.maximum_warning_rate:
            failure_reasons.append(
                f"Warning rate {warning_rate:.2%} exceeds "
                f"maximum {self._criteria.maximum_warning_rate:.2%}"
            )

        if summary.health_score < self._criteria.minimum_health_score:
            failure_reasons.append(
                f"Health score {summary.health_score:.2f} is below "
                f"minimum {self._criteria.minimum_health_score:.2f}"
            )

        outcome = (
            HardwareTestOutcome.FAIL
            if failure_reasons
            else HardwareTestOutcome.PASS
        )

        return HardwareTestResult(
            sensor_id=sensor_id,
            sensor_type=sensor_type,
            outcome=outcome,
            total_readings=summary.total_readings,
            normal_count=summary.normal_count,
            warning_count=summary.warning_count,
            fault_count=summary.fault_count,
            warning_rate=round(warning_rate, 4),
            health_score=summary.health_score,
            failure_reasons=tuple(failure_reasons),
        )
