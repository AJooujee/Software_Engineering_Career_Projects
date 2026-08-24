"""Tests for sensor fault detection and health analysis."""

from datetime import datetime, timezone

import pytest

from sensor_platform.analysis import FaultDetector, SensorThreshold
from sensor_platform.models import SensorReading, SensorStatus, SensorType


def make_reading(
    sensor_type: SensorType,
    value: float,
) -> SensorReading:
    """Create a reading with a predictable value for analysis tests."""

    units = {
        SensorType.TEMPERATURE: "C",
        SensorType.VOLTAGE: "V",
        SensorType.CURRENT: "A",
        SensorType.VIBRATION: "mm/s",
    }

    return SensorReading(
        sensor_id=f"{sensor_type.value}-test",
        sensor_type=sensor_type,
        value=value,
        unit=units[sensor_type],
        timestamp=datetime.now(timezone.utc),
    )


@pytest.mark.parametrize(
    ("sensor_type", "value", "expected_status"),
    [
        (SensorType.TEMPERATURE, 25.0, SensorStatus.NORMAL),
        (SensorType.TEMPERATURE, 33.0, SensorStatus.WARNING),
        (SensorType.TEMPERATURE, 40.0, SensorStatus.FAULT),
        (SensorType.VOLTAGE, 11.0, SensorStatus.WARNING),
        (SensorType.VIBRATION, 8.0, SensorStatus.FAULT),
    ],
)
def test_fault_detector_classifies_readings(
    sensor_type: SensorType,
    value: float,
    expected_status: SensorStatus,
) -> None:
    """Readings should receive the correct health classification."""

    result = FaultDetector().analyze(
        make_reading(sensor_type, value)
    )

    assert result.reading.status == expected_status
    assert result.deviation_from_normal >= 0


def test_health_summary_calculates_counts_and_score() -> None:
    """The summary should aggregate normal, warning, and fault results."""

    detector = FaultDetector()
    readings = [
        make_reading(SensorType.TEMPERATURE, 25.0),
        make_reading(SensorType.TEMPERATURE, 33.0),
        make_reading(SensorType.TEMPERATURE, 40.0),
    ]

    summary = detector.summarize(
        detector.analyze_many(readings)
    )

    assert summary.total_readings == 3
    assert summary.normal_count == 1
    assert summary.warning_count == 1
    assert summary.fault_count == 1
    assert summary.health_score == 50.0


def test_sensor_threshold_rejects_invalid_order() -> None:
    """Threshold configuration must progress from low to high."""

    with pytest.raises(ValueError, match="must be ordered"):
        SensorThreshold(
            critical_minimum=20.0,
            normal_minimum=10.0,
            normal_maximum=30.0,
            critical_maximum=40.0,
        )
