"""Data-access operations for sensor readings."""

from collections.abc import Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from sensor_platform.db_models import SensorReadingRecord
from sensor_platform.models import SensorReading


class SensorReadingRepository:
    """Store and retrieve sensor readings from the database."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
    ) -> None:
        self._session_factory = session_factory

    def save(self, reading: SensorReading) -> int:
        """Save one reading and return its database ID."""

        record = SensorReadingRecord.from_domain(reading)

        with self._session_factory() as session:
            session.add(record)
            session.commit()

        return record.id

    def save_many(
        self,
        readings: Iterable[SensorReading],
    ) -> list[int]:
        """Save multiple readings in one database transaction."""

        records = [
            SensorReadingRecord.from_domain(reading)
            for reading in readings
        ]

        if not records:
            return []

        with self._session_factory() as session:
            session.add_all(records)
            session.commit()

        return [record.id for record in records]

    def list_all(self, limit: int | None = None) -> list[SensorReading]:
        """Return stored readings ordered from oldest to newest."""

        if limit is not None and limit <= 0:
            raise ValueError("limit must be greater than zero")

        statement = select(SensorReadingRecord).order_by(
            SensorReadingRecord.timestamp,
            SensorReadingRecord.id,
        )

        if limit is not None:
            statement = statement.limit(limit)

        with self._session_factory() as session:
            records = session.scalars(statement).all()

        return [record.to_domain() for record in records]

    def count(self) -> int:
        """Return the total number of stored sensor readings."""

        statement = select(func.count()).select_from(
            SensorReadingRecord
        )

        with self._session_factory() as session:
            total = session.scalar(statement)

        return int(total or 0)
