"""Export automated hardware test reports to JSON and CSV."""

import csv
import json
from pathlib import Path

from sensor_platform.hardware_testing import HardwareTestReport


def export_json_report(
    report: HardwareTestReport,
    output_path: str | Path,
) -> Path:
    """Write a complete hardware test report as formatted JSON."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(report.to_dict(), indent=2),
        encoding="utf-8",
    )

    return path


def export_csv_report(
    report: HardwareTestReport,
    output_path: str | Path,
) -> Path:
    """Write one CSV row for each tested sensor."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "overall_outcome",
        "sensor_id",
        "sensor_type",
        "outcome",
        "total_readings",
        "normal_count",
        "warning_count",
        "fault_count",
        "warning_rate",
        "health_score",
        "failure_reasons",
    ]

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
        )
        writer.writeheader()

        for result in report.results:
            writer.writerow(
                {
                    "overall_outcome": report.overall_outcome.value,
                    "sensor_id": result.sensor_id,
                    "sensor_type": result.sensor_type.value,
                    "outcome": result.outcome.value,
                    "total_readings": result.total_readings,
                    "normal_count": result.normal_count,
                    "warning_count": result.warning_count,
                    "fault_count": result.fault_count,
                    "warning_rate": result.warning_rate,
                    "health_score": result.health_score,
                    "failure_reasons": " | ".join(
                        result.failure_reasons
                    ),
                }
            )

    return path
