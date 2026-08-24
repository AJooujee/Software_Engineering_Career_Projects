"""Command-line interface for sensor simulation and analysis."""

import argparse
import json
import sys
from pathlib import Path

from sensor_platform.analysis import FaultDetector
from sensor_platform.database import (
    create_database_engine,
    create_session_factory,
    initialize_database,
)
from sensor_platform.models import SensorReading, SensorType
from sensor_platform.repository import SensorReadingRepository
from sensor_platform.simulator import SensorSimulator


def build_parser() -> argparse.ArgumentParser:
    """Create and configure command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Generate and analyze hardware sensor readings."
    )
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--warning-rate",
        type=float,
        default=0.0,
        help="Probability of generating a warning reading.",
    )
    parser.add_argument(
        "--fault-rate",
        type=float,
        default=0.0,
        help="Probability of generating a fault reading.",
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=None,
        help="Optional SQLite file used to store analyzed readings.",
    )
    return parser


def save_readings(
    readings: list[SensorReading],
    database_path: Path,
) -> None:
    """Save analyzed sensor readings to SQLite."""

    engine = create_database_engine(database_path)

    try:
        initialize_database(engine)
        repository = SensorReadingRepository(
            create_session_factory(engine)
        )
        repository.save_many(readings)
    finally:
        engine.dispose()


def main() -> None:
    """Generate, analyze, optionally save, and print sensor readings."""

    parser = build_parser()
    args = parser.parse_args()

    if args.count <= 0:
        parser.error("--count must be greater than zero")

    for name, rate in (
        ("--warning-rate", args.warning_rate),
        ("--fault-rate", args.fault_rate),
    ):
        if not 0 <= rate <= 1:
            parser.error(f"{name} must be between 0 and 1")

    if args.warning_rate + args.fault_rate > 1:
        parser.error(
            "--warning-rate and --fault-rate cannot total more than 1"
        )

    raw_readings: list[SensorReading] = []

    # Generate a configurable mixture of normal and abnormal readings.
    for index, sensor_type in enumerate(SensorType):
        simulator = SensorSimulator(
            sensor_id=f"{sensor_type.value}-001",
            sensor_type=sensor_type,
            seed=args.seed + index,
        )
        raw_readings.extend(
            simulator.generate_batch(
                count=args.count,
                warning_rate=args.warning_rate,
                fault_rate=args.fault_rate,
            )
        )

    # Assign a diagnostic status based on hardware safety thresholds.
    detector = FaultDetector()
    results = detector.analyze_many(raw_readings)
    summary = detector.summarize(results)
    analyzed_readings = [result.reading for result in results]

    if args.database is not None:
        save_readings(analyzed_readings, args.database)
        print(
            f"Saved {len(analyzed_readings)} readings "
            f"to {args.database}",
            file=sys.stderr,
        )

    # Operational messages use stderr so stdout remains valid JSON.
    print(
        f"Health score: {summary.health_score}% | "
        f"Normal: {summary.normal_count} | "
        f"Warning: {summary.warning_count} | "
        f"Fault: {summary.fault_count}",
        file=sys.stderr,
    )

    print(
        json.dumps(
            [reading.to_dict() for reading in analyzed_readings],
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
