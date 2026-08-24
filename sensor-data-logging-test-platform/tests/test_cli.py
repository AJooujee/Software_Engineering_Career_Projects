import json
import sys

from sensor_platform.cli import main


def test_cli_generates_all_sensor_types(monkeypatch, capsys) -> None:
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
