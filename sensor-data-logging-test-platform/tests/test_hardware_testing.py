"""Tests for automated hardware pass/fail evaluation."""

import pytest

from sensor_platform.hardware_testing import (
    HardwareTestCriteria,
    HardwareTestRunner,
    HardwareTestOutcome,
)
from sensor_platform.models import SensorType
from sensor_platform.simulator import SensorSimulator


def create_batch(
    sensor_id: str,
    sensor_type: SensorType,
    *,
    count: int = 5,
    warning_rate: float = 0.0,
    fault_rate: float = 0.0,
):
    """Create a deterministic batch for hardware testing."""

    return SensorSimulator(
        sensor_id,
        sensor_type,
        seed=42,
    ).generate_batch(
        count,
        warning_rate=warning_rate,
        fault_rate=fault_rate,
    )


def test_normal_sensor_passes_hardware_test() -> None:
    """A healthy sensor with enough readings should pass."""

    report = HardwareTestRunner().run(
        create_batch(
            "temperature-001",
            SensorType.TEMPERATURE,
        )
    )

    assert report.overall_outcome == HardwareTestOutcome.PASS
    assert report.passed_sensors == 1
    assert report.failed_sensors == 0
    assert report.results[0].failure_reasons == ()


def test_faulty_sensor_fails_hardware_test() -> None:
    """A sensor containing critical faults should fail."""

    report = HardwareTestRunner().run(
        create_batch(
            "voltage-001",
            SensorType.VOLTAGE,
            fault_rate=1.0,
        )
    )

    result = report.results[0]

    assert result.outcome == HardwareTestOutcome.FAIL
    assert result.fault_count == 5
    assert any(
        "Fault count" in reason
        for reason in result.failure_reasons
    )


def test_sensor_fails_with_insufficient_readings() -> None:
    """A sensor should fail when the sample size is too small."""

    report = HardwareTestRunner().run(
        create_batch(
            "current-001",
            SensorType.CURRENT,
            count=2,
        )
    )

    assert report.results[0].outcome == HardwareTestOutcome.FAIL
    assert any(
        "Insufficient readings" in reason
        for reason in report.results[0].failure_reasons
    )


def test_report_combines_passing_and_failing_sensors() -> None:
    """The overall report should fail if any sensor fails."""

    normal_readings = create_batch(
        "temperature-001",
        SensorType.TEMPERATURE,
    )
    fault_readings = create_batch(
        "vibration-001",
        SensorType.VIBRATION,
        fault_rate=1.0,
    )

    report = HardwareTestRunner().run(
        normal_readings + fault_readings
    )

    assert report.overall_outcome == HardwareTestOutcome.FAIL
    assert report.total_sensors == 2
    assert report.passed_sensors == 1
    assert report.failed_sensors == 1


def test_hardware_criteria_rejects_invalid_values() -> None:
    """Negative fault allowances should not be accepted."""

    with pytest.raises(
        ValueError,
        match="maximum_fault_count cannot be negative",
    ):
        HardwareTestCriteria(maximum_fault_count=-1)
