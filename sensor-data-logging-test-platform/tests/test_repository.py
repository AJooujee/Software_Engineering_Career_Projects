"""Tests for SQLite sensor data storage."""

from datetime import datetime, timezone

import pytest

from sensor_platform.database import (
    create_database_engine,
    create_session_factory,
    initialize_database,
)
from sensor_platform.models import SensorReading, SensorStatus, SensorType
from sensor_platform.repository import SensorReadingRepository
from sensor_platform.simulator import SensorSimulator


@pytest.fixture
def repository(tmp_path):
    """Create an isolated SQLite database for each test."""

    engine = create_database_engine(tmp_path / "test_sensor_data.db")
    initialize_database(engine)

    repository = SensorReadingRepository(
        create_session_factory(engine)
    )

    yield repository
    engine.dispose()


def test_save_and_retrieve_reading(repository) -> None:
    """A stored reading should be returned without losing information."""

    reading = SensorReading(
        sensor_id="temperature-001",
        sensor_type=SensorType.TEMPERATURE,
        value=24.5,
        unit="C",
        timestamp=datetime.now(timezone.utc),
        status=SensorStatus.NORMAL,
    )

    record_id = repository.save(reading)
    stored_readings = repository.list_all()

    assert record_id == 1
    assert repository.count() == 1
    assert stored_readings == [reading]


def test_save_many_sensor_readings(repository) -> None:
    """A generated batch should be stored in one transaction."""

    simulator = SensorSimulator(
        sensor_id="voltage-001",
        sensor_type=SensorType.VOLTAGE,
        seed=42,
    )
    readings = simulator.generate_batch(5)

    record_ids = repository.save_many(readings)

    assert record_ids == [1, 2, 3, 4, 5]
    assert repository.count() == 5
    assert repository.list_all() == readings


def test_list_all_rejects_invalid_limit(repository) -> None:
    """The repository should reject invalid query limits."""

    with pytest.raises(ValueError, match="greater than zero"):
        repository.list_all(limit=0)
