"""Tests for JSON and CSV hardware report export."""

import csv
import json

from sensor_platform.hardware_testing import HardwareTestRunner
from sensor_platform.models import SensorType
from sensor_platform.reporting import (
    export_csv_report,
    export_json_report,
)
from sensor_platform.simulator import SensorSimulator


def create_report():
    """Create a report containing one passing and one failing sensor."""

    normal_readings = SensorSimulator(
        "temperature-001",
        SensorType.TEMPERATURE,
        seed=42,
    ).generate_batch(5)

    fault_readings = SensorSimulator(
        "voltage-001",
        SensorType.VOLTAGE,
        seed=43,
    ).generate_batch(5, fault_rate=1.0)

    return HardwareTestRunner().run(
        normal_readings + fault_readings
    )


def test_export_json_report(tmp_path) -> None:
    """The JSON report should preserve the complete test result."""

    path = export_json_report(
        create_report(),
        tmp_path / "report.json",
    )
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["overall_outcome"] == "fail"
    assert payload["total_sensors"] == 2
    assert len(payload["results"]) == 2


def test_export_csv_report(tmp_path) -> None:
    """The CSV report should contain one row per tested sensor."""

    path = export_csv_report(
        create_report(),
        tmp_path / "report.csv",
    )

    with path.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert len(rows) == 2
    assert {row["outcome"] for row in rows} == {"pass", "fail"}
