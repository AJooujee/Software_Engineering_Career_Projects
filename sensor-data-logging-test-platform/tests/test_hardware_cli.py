"""Tests for the automated hardware testing CLI."""

import json
import sys

from sensor_platform.hardware_cli import main


def test_hardware_cli_exports_passing_report(
    monkeypatch,
    capsys,
    tmp_path,
) -> None:
    """A normal simulation should produce passing report files."""

    json_path = tmp_path / "passing.json"
    csv_path = tmp_path / "passing.csv"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "sensor-test",
            "--count",
            "5",
            "--json-report",
            str(json_path),
            "--csv-report",
            str(csv_path),
        ],
    )

    main()
    summary = json.loads(capsys.readouterr().out)

    assert summary["overall_outcome"] == "pass"
    assert summary["passed_sensors"] == 4
    assert json_path.exists()
    assert csv_path.exists()


def test_hardware_cli_exports_failing_report(
    monkeypatch,
    capsys,
    tmp_path,
) -> None:
    """Injected faults should produce a failing report."""

    json_path = tmp_path / "failing.json"
    csv_path = tmp_path / "failing.csv"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "sensor-test",
            "--count",
            "5",
            "--fault-rate",
            "1.0",
            "--json-report",
            str(json_path),
            "--csv-report",
            str(csv_path),
        ],
    )

    main()
    summary = json.loads(capsys.readouterr().out)

    assert summary["overall_outcome"] == "fail"
    assert summary["failed_sensors"] == 4
    assert json_path.exists()
    assert csv_path.exists()
