"""Generate normal, warning, and fault sensor readings."""

import random
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from sensor_platform.models import SensorReading, SensorStatus, SensorType


class SimulationMode(str, Enum):
    """Operating condition used when generating a sensor value."""

    NORMAL = "normal"
    WARNING = "warning"
    FAULT = "fault"


@dataclass(frozen=True, slots=True)
class SensorConfig:
    """Numeric range and unit used by a simulated sensor."""

    minimum: float
    maximum: float
    unit: str


NORMAL_CONFIGS: dict[SensorType, SensorConfig] = {
    SensorType.TEMPERATURE: SensorConfig(20.0, 30.0, "C"),
    SensorType.VOLTAGE: SensorConfig(11.5, 12.5, "V"),
    SensorType.CURRENT: SensorConfig(0.5, 5.0, "A"),
    SensorType.VIBRATION: SensorConfig(0.0, 4.0, "mm/s"),
}

WARNING_CONFIGS: dict[SensorType, SensorConfig] = {
    SensorType.TEMPERATURE: SensorConfig(30.1, 34.9, "C"),
    SensorType.VOLTAGE: SensorConfig(12.6, 13.4, "V"),
    SensorType.CURRENT: SensorConfig(5.1, 6.9, "A"),
    SensorType.VIBRATION: SensorConfig(4.1, 6.9, "mm/s"),
}

FAULT_CONFIGS: dict[SensorType, SensorConfig] = {
    SensorType.TEMPERATURE: SensorConfig(35.1, 45.0, "C"),
    SensorType.VOLTAGE: SensorConfig(13.6, 15.0, "V"),
    SensorType.CURRENT: SensorConfig(7.1, 10.0, "A"),
    SensorType.VIBRATION: SensorConfig(7.1, 12.0, "mm/s"),
}

MODE_CONFIGS = {
    SimulationMode.NORMAL: NORMAL_CONFIGS,
    SimulationMode.WARNING: WARNING_CONFIGS,
    SimulationMode.FAULT: FAULT_CONFIGS,
}


class SensorSimulator:
    """Generate repeatable readings for one hardware sensor."""

    def __init__(
        self,
        sensor_id: str,
        sensor_type: SensorType,
        seed: int | None = None,
    ) -> None:
        if not sensor_id.strip():
            raise ValueError("sensor_id cannot be empty")

        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self._random = random.Random(seed)

    def generate_reading(
        self,
        mode: SimulationMode = SimulationMode.NORMAL,
    ) -> SensorReading:
        """Generate one reading for the requested operating condition."""

        config = MODE_CONFIGS[mode][self.sensor_type]
        value = round(
            self._random.uniform(config.minimum, config.maximum),
            3,
        )

        # The analysis engine assigns the final diagnostic status later.
        return SensorReading(
            sensor_id=self.sensor_id,
            sensor_type=self.sensor_type,
            value=value,
            unit=config.unit,
            timestamp=datetime.now(timezone.utc),
            status=SensorStatus.NORMAL,
        )

    def generate_batch(
        self,
        count: int,
        warning_rate: float = 0.0,
        fault_rate: float = 0.0,
    ) -> list[SensorReading]:
        """Generate readings with optional warning and fault injection."""

        if count <= 0:
            raise ValueError("count must be greater than zero")

        self._validate_rate("warning_rate", warning_rate)
        self._validate_rate("fault_rate", fault_rate)

        if warning_rate + fault_rate > 1:
            raise ValueError(
                "warning_rate and fault_rate cannot total more than 1"
            )

        readings = []

        for _ in range(count):
            probability = self._random.random()

            if probability < fault_rate:
                mode = SimulationMode.FAULT
            elif probability < fault_rate + warning_rate:
                mode = SimulationMode.WARNING
            else:
                mode = SimulationMode.NORMAL

            readings.append(self.generate_reading(mode))

        return readings

    @staticmethod
    def _validate_rate(name: str, rate: float) -> None:
        """Ensure an injection rate is a probability from zero to one."""

        if not 0 <= rate <= 1:
            raise ValueError(f"{name} must be between 0 and 1")
