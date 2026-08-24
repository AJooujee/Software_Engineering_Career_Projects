"""SQLAlchemy models used to store sensor readings."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from sensor_platform.database import Base
from sensor_platform.models import SensorReading, SensorStatus, SensorType


class SensorReadingRecord(Base):
    """Database representation of one hardware sensor reading."""

    __tablename__ = "sensor_readings"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    sensor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    sensor_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    @classmethod
    def from_domain(
        cls,
        reading: SensorReading,
    ) -> "SensorReadingRecord":
        """Convert a SensorReading object into a database record."""

        return cls(
            sensor_id=reading.sensor_id,
            sensor_type=reading.sensor_type.value,
            value=reading.value,
            unit=reading.unit,
            timestamp=reading.timestamp,
            status=reading.status.value,
        )

    def to_domain(self) -> SensorReading:
        """Convert a database record back into a SensorReading object."""

        timestamp = self.timestamp

        # SQLite may return a datetime without timezone information.
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        return SensorReading(
            sensor_id=self.sensor_id,
            sensor_type=SensorType(self.sensor_type),
            value=self.value,
            unit=self.unit,
            timestamp=timestamp,
            status=SensorStatus(self.status),
        )
