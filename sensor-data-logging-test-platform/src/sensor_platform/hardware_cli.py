"""Command-line interface for automated hardware testing."""

import argparse
import json
from pathlib import Path

from sensor_platform.hardware_testing import (
    HardwareTestCriteria,
    HardwareTestRunner,
)
from sensor_platform.models import SensorReading, SensorType
from sensor_platform.reporting import (
    export_csv_report,
    export_json_report,
)
from sensor_platform.simulator import SensorSimulator


def build_parser() -> argparse.ArgumentParser:
    """Create command-line arguments for the hardware test runner."""

    parser = argparse.ArgumentParser(
        description="Run automated pass/fail hardware sensor tests."
    )
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--warning-rate", type=float, default=0.0)
    parser.add_argument("--fault-rate", type=float, default=0.0)
    parser.add_argument("--minimum-readings", type=int, default=5)
    parser.add_argument("--maximum-fault-count", type=int, default=0)
    parser.add_argument("--maximum-warning-rate", type=float, default=0.20)
    parser.add_argument("--minimum-health-score", type=float, default=80.0)
    parser.add_argument(
        "--json-report",
        type=Path,
        default=Path("reports") / "hardware_test_report.json",
    )
    parser.add_argument(
        "--csv-report",
        type=Path,
        default=Path("reports") / "hardware_test_report.csv",
    )
    return parser


def main() -> None:
    """Generate readings, execute tests, and export reports."""

    args = build_parser().parse_args()

    if args.count <= 0:
        raise ValueError("--count must be greater than zero")

    readings: list[SensorReading] = []

    # Generate an independent test batch for every sensor type.
    for index, sensor_type in enumerate(SensorType):
        simulator = SensorSimulator(
            sensor_id=f"{sensor_type.value}-001",
            sensor_type=sensor_type,
            seed=args.seed + index,
        )
        readings.extend(
            simulator.generate_batch(
                count=args.count,
                warning_rate=args.warning_rate,
                fault_rate=args.fault_rate,
            )
        )

    criteria = HardwareTestCriteria(
        minimum_readings=args.minimum_readings,
        maximum_fault_count=args.maximum_fault_count,
        maximum_warning_rate=args.maximum_warning_rate,
        minimum_health_score=args.minimum_health_score,
    )

    report = HardwareTestRunner(criteria=criteria).run(readings)

    json_path = export_json_report(report, args.json_report)
    csv_path = export_csv_report(report, args.csv_report)

    # Print a concise machine-readable summary to the terminal.
    print(
        json.dumps(
            {
                "overall_outcome": report.overall_outcome.value,
                "total_sensors": report.total_sensors,
                "passed_sensors": report.passed_sensors,
                "failed_sensors": report.failed_sensors,
                "json_report": str(json_path),
                "csv_report": str(csv_path),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
