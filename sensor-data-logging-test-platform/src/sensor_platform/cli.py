"""Command-line interface for generating and storing sensor data."""

import argparse
import json
import sys
from pathlib import Path

from sensor_platform.database import (
    create_database_engine,
    create_session_factory,
    initialize_database,
)
from sensor_platform.models import SensorReading, SensorType
from sensor_platform.repository import SensorReadingRepository
from sensor_platform.simulator import SensorSimulator


def build_parser() -> argparse.ArgumentParser:
    """Create and configure the command-line argument parser."""

    parser = argparse.ArgumentParser(
        description="Generate simulated hardware sensor readings."
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of readings generated for each sensor type.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed used to produce repeatable data.",
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=None,
        help="Optional SQLite file used to store generated readings.",
    )
    return parser


def save_readings(
    readings: list[SensorReading],
    database_path: Path,
) -> None:
    """Save generated readings to the selected SQLite database."""

    engine = create_database_engine(database_path)

    try:
        initialize_database(engine)
        repository = SensorReadingRepository(
            create_session_factory(engine)
        )
        repository.save_many(readings)
    finally:
        # Always close database connections, even if saving fails.
        engine.dispose()


def main() -> None:
    """Generate sensor readings, optionally save them, and print JSON."""

    parser = build_parser()
    args = parser.parse_args()

    if args.count <= 0:
        parser.error("--count must be greater than zero")

    readings: list[SensorReading] = []

    # Generate one batch for every supported hardware sensor type.
    for index, sensor_type in enumerate(SensorType):
        simulator = SensorSimulator(
            sensor_id=f"{sensor_type.value}-001",
            sensor_type=sensor_type,
            seed=args.seed + index,
        )
        readings.extend(simulator.generate_batch(args.count))

    if args.database is not None:
        save_readings(readings, args.database)

        # Diagnostic messages use stderr so stdout remains valid JSON.
        print(
            f"Saved {len(readings)} readings to {args.database}",
            file=sys.stderr,
        )

    print(
        json.dumps(
            [reading.to_dict() for reading in readings],
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
