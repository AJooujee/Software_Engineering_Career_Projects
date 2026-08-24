import random
from dataclasses import dataclass
from datetime import datetime, timezone

from sensor_platform.models import SensorReading, SensorStatus, SensorType


@dataclass(frozen=True, slots=True)
class SensorConfig:
    minimum: float
    maximum: float
    unit: str


SENSOR_CONFIGS: dict[SensorType, SensorConfig] = {
    SensorType.TEMPERATURE: SensorConfig(20.0, 30.0, "C"),
    SensorType.VOLTAGE: SensorConfig(11.5, 12.5, "V"),
    SensorType.CURRENT: SensorConfig(0.5, 5.0, "A"),
    SensorType.VIBRATION: SensorConfig(0.0, 4.0, "mm/s"),
}


class SensorSimulator:
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

    def generate_reading(self) -> SensorReading:
        config = SENSOR_CONFIGS[self.sensor_type]
        value = round(
            self._random.uniform(config.minimum, config.maximum),
            3,
        )

        return SensorReading(
            sensor_id=self.sensor_id,
            sensor_type=self.sensor_type,
            value=value,
            unit=config.unit,
            timestamp=datetime.now(timezone.utc),
            status=SensorStatus.NORMAL,
        )

    def generate_batch(self, count: int) -> list[SensorReading]:
        if count <= 0:
            raise ValueError("count must be greater than zero")

        return [self.generate_reading() for _ in range(count)]
