from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class SensorType(str, Enum):
    TEMPERATURE = "temperature"
    VOLTAGE = "voltage"
    CURRENT = "current"
    VIBRATION = "vibration"


class SensorStatus(str, Enum):
    NORMAL = "normal"
    WARNING = "warning"
    FAULT = "fault"


@dataclass(frozen=True, slots=True)
class SensorReading:
    sensor_id: str
    sensor_type: SensorType
    value: float
    unit: str
    timestamp: datetime
    status: SensorStatus = SensorStatus.NORMAL

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["sensor_type"] = self.sensor_type.value
        payload["status"] = self.status.value
        payload["timestamp"] = self.timestamp.isoformat()
        return payload
