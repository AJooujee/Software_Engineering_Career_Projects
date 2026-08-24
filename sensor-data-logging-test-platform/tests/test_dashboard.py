"""Tests for dashboard data preparation and charts."""

from datetime import datetime, timezone

import pandas as pd

from sensor_platform.dashboard import (
    build_status_figure,
    build_time_series_figure,
    calculate_dashboard_metrics,
    readings_to_dataframe,
)
from sensor_platform.models import SensorReading, SensorStatus, SensorType


def create_dashboard_readings() -> list[SensorReading]:
    """Create readings covering every diagnostic status."""

    timestamp = datetime.now(timezone.utc)

    return [
        SensorReading(
            "temperature-001",
            SensorType.TEMPERATURE,
            25.0,
            "C",
            timestamp,
            SensorStatus.NORMAL,
        ),
        SensorReading(
            "temperature-001",
            SensorType.TEMPERATURE,
            33.0,
            "C",
            timestamp,
            SensorStatus.WARNING,
        ),
        SensorReading(
            "temperature-001",
            SensorType.TEMPERATURE,
            40.0,
            "C",
            timestamp,
            SensorStatus.FAULT,
        ),
    ]


def test_dashboard_dataframe_and_metrics() -> None:
    """Dashboard metrics should match the supplied readings."""

    frame = readings_to_dataframe(
        create_dashboard_readings()
    )
    metrics = calculate_dashboard_metrics(frame)

    assert list(frame.columns) == [
        "timestamp",
        "sensor_id",
        "sensor_type",
        "value",
        "unit",
        "status",
    ]
    assert metrics["total"] == 3
    assert metrics["normal"] == 1
    assert metrics["warning"] == 1
    assert metrics["fault"] == 1
    assert metrics["health_score"] == 50.0


def test_empty_dashboard_metrics() -> None:
    """An empty dataset should return zero-valued metrics."""

    frame = pd.DataFrame(
        columns=[
            "timestamp",
            "sensor_id",
            "sensor_type",
            "value",
            "unit",
            "status",
        ]
    )

    assert calculate_dashboard_metrics(frame)["total"] == 0


def test_dashboard_builds_plotly_figures() -> None:
    """Time-series and status charts should contain plotted data."""

    frame = readings_to_dataframe(
        create_dashboard_readings()
    )

    time_series = build_time_series_figure(frame)
    status_chart = build_status_figure(frame)

    assert len(time_series.data) >= 1
    assert len(status_chart.data) == 1
