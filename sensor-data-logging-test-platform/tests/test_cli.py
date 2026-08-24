"""Tests for the sensor simulator command-line interface."""

import json
import sys

from sensor_platform.cli import main
from sensor_platform.database import (
    create_database_engine,
    create_session_factory,
    initialize_database,
)
from sensor_platform.repository import SensorReadingRepository


def test_cli_generates_all_sensor_types(monkeypatch, capsys) -> None:
    """The CLI should generate readings for all four sensor types."""

    monkeypatch.setattr(
        sys,
        "argv",
        ["sensor-sim", "--count", "2", "--seed", "42"],
    )

    main()
    output = json.loads(capsys.readouterr().out)

    assert len(output) == 8
    assert {item["sensor_type"] for item in output} == {
        "temperature",
        "voltage",
        "current",
        "vibration",
    }


def test_cli_saves_generated_readings(
    monkeypatch,
    capsys,
    tmp_path,
) -> None:
    """The CLI should persist generated readings when given a database."""

    database_path = tmp_path / "cli_sensor_data.db"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "sensor-sim",
            "--count",
            "2",
            "--seed",
            "42",
            "--database",
            str(database_path),
        ],
    )

    main()
    captured = capsys.readouterr()

    # Four sensor types multiplied by two readings each equals eight.
    assert "Saved 8 readings" in captured.err

    engine = create_database_engine(database_path)
    initialize_database(engine)
    repository = SensorReadingRepository(
        create_session_factory(engine)
    )

    try:
        assert repository.count() == 8
    finally:
        engine.dispose()
