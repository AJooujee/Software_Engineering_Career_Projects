"""Tests for simulated warning and fault injection."""

import pytest

from sensor_platform.analysis import FaultDetector
from sensor_platform.models import SensorStatus, SensorType
from sensor_platform.simulator import SensorSimulator


def test_warning_rate_generates_warning_readings() -> None:
    """A 100 percent warning rate should produce only warnings."""

    simulator = SensorSimulator(
        "temperature-001",
        SensorType.TEMPERATURE,
        seed=42,
    )
    results = FaultDetector().analyze_many(
        simulator.generate_batch(5, warning_rate=1.0)
    )

    assert all(
        result.reading.status == SensorStatus.WARNING
        for result in results
    )


def test_fault_rate_generates_fault_readings() -> None:
    """A 100 percent fault rate should produce only faults."""

    simulator = SensorSimulator(
        "voltage-001",
        SensorType.VOLTAGE,
        seed=42,
    )
    results = FaultDetector().analyze_many(
        simulator.generate_batch(5, fault_rate=1.0)
    )

    assert all(
        result.reading.status == SensorStatus.FAULT
        for result in results
    )


@pytest.mark.parametrize(
    ("warning_rate", "fault_rate"),
    [
        (-0.1, 0.0),
        (0.0, 1.1),
        (0.6, 0.5),
    ],
)
def test_generate_batch_rejects_invalid_rates(
    warning_rate: float,
    fault_rate: float,
) -> None:
    """Injection probabilities must form a valid distribution."""

    simulator = SensorSimulator(
        "current-001",
        SensorType.CURRENT,
    )

    with pytest.raises(ValueError):
        simulator.generate_batch(
            5,
            warning_rate=warning_rate,
            fault_rate=fault_rate,
        )
