import pytest

from sensor_platform.models import SensorStatus, SensorType
from sensor_platform.simulator import SensorSimulator


@pytest.mark.parametrize(
    ("sensor_type", "minimum", "maximum", "unit"),
    [
        (SensorType.TEMPERATURE, 20.0, 30.0, "C"),
        (SensorType.VOLTAGE, 11.5, 12.5, "V"),
        (SensorType.CURRENT, 0.5, 5.0, "A"),
        (SensorType.VIBRATION, 0.0, 4.0, "mm/s"),
    ],
)
def test_generate_reading(
    sensor_type: SensorType,
    minimum: float,
    maximum: float,
    unit: str,
) -> None:
    simulator = SensorSimulator("sensor-001", sensor_type, seed=42)

    reading = simulator.generate_reading()

    assert reading.sensor_id == "sensor-001"
    assert reading.sensor_type == sensor_type
    assert minimum <= reading.value <= maximum
    assert reading.unit == unit
    assert reading.status == SensorStatus.NORMAL
    assert reading.timestamp.tzinfo is not None


def test_generate_batch_returns_requested_count() -> None:
    simulator = SensorSimulator(
        "temperature-001",
        SensorType.TEMPERATURE,
        seed=42,
    )

    readings = simulator.generate_batch(10)

    assert len(readings) == 10


def test_seed_produces_repeatable_values() -> None:
    first = SensorSimulator("voltage-001", SensorType.VOLTAGE, seed=42)
    second = SensorSimulator("voltage-001", SensorType.VOLTAGE, seed=42)

    first_values = [reading.value for reading in first.generate_batch(3)]
    second_values = [reading.value for reading in second.generate_batch(3)]

    assert first_values == second_values


def test_generate_batch_rejects_invalid_count() -> None:
    simulator = SensorSimulator("current-001", SensorType.CURRENT)

    with pytest.raises(ValueError, match="greater than zero"):
        simulator.generate_batch(0)
