"""Interactive Streamlit dashboard for sensor test analysis."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from sensor_platform.database import (
    create_database_engine,
    create_session_factory,
    initialize_database,
)
from sensor_platform.models import SensorReading
from sensor_platform.repository import SensorReadingRepository


DASHBOARD_COLUMNS = [
    "timestamp",
    "sensor_id",
    "sensor_type",
    "value",
    "unit",
    "status",
]


def load_readings(
    database_path: str | Path,
) -> list[SensorReading]:
    """Load all available readings from a SQLite database."""

    path = Path(database_path)

    if not path.exists():
        return []

    engine = create_database_engine(path)

    try:
        initialize_database(engine)
        repository = SensorReadingRepository(
            create_session_factory(engine)
        )
        return repository.list_all()
    finally:
        engine.dispose()


def readings_to_dataframe(
    readings: list[SensorReading],
) -> pd.DataFrame:
    """Convert domain objects into dashboard-ready tabular data."""

    records = [
        {
            "timestamp": reading.timestamp,
            "sensor_id": reading.sensor_id,
            "sensor_type": reading.sensor_type.value,
            "value": reading.value,
            "unit": reading.unit,
            "status": reading.status.value,
        }
        for reading in readings
    ]

    frame = pd.DataFrame(
        records,
        columns=DASHBOARD_COLUMNS,
    )

    if not frame.empty:
        # UTC conversion keeps timestamps consistent across environments.
        frame["timestamp"] = pd.to_datetime(
            frame["timestamp"],
            utc=True,
        )

    return frame


def calculate_dashboard_metrics(
    frame: pd.DataFrame,
) -> dict[str, int | float]:
    """Calculate status totals and overall health score."""

    total = len(frame)

    if total == 0:
        return {
            "total": 0,
            "normal": 0,
            "warning": 0,
            "fault": 0,
            "health_score": 0.0,
        }

    status_counts = frame["status"].value_counts()
    normal = int(status_counts.get("normal", 0))
    warning = int(status_counts.get("warning", 0))
    fault = int(status_counts.get("fault", 0))

    # Warning readings receive half credit in the health calculation.
    health_score = round(
        ((normal + warning * 0.5) / total) * 100,
        2,
    )

    return {
        "total": total,
        "normal": normal,
        "warning": warning,
        "fault": fault,
        "health_score": health_score,
    }


def build_time_series_figure(frame: pd.DataFrame):
    """Build a time-series graph grouped by sensor and sensor type."""

    figure = px.line(
        frame,
        x="timestamp",
        y="value",
        color="sensor_id",
        facet_row="sensor_type",
        markers=True,
        title="Sensor Readings Over Time",
    )

    # Each sensor type uses a different unit and therefore its own scale.
    figure.update_yaxes(matches=None)
    figure.update_layout(
        height=750,
        legend_title_text="Sensor",
    )

    return figure


def build_status_figure(frame: pd.DataFrame):
    """Build a donut chart showing sensor health distribution."""

    status_counts = (
        frame["status"]
        .value_counts()
        .rename_axis("status")
        .reset_index(name="count")
    )

    figure = px.pie(
        status_counts,
        names="status",
        values="count",
        hole=0.55,
        title="Sensor Status Distribution",
        color="status",
        color_discrete_map={
            "normal": "#2ecc71",
            "warning": "#f39c12",
            "fault": "#e74c3c",
        },
    )

    return figure


def main() -> None:
    """Render the interactive sensor monitoring dashboard."""

    st.set_page_config(
        page_title="Sensor Test Dashboard",
        page_icon="📡",
        layout="wide",
    )

    st.title("Sensor Data Logging & Hardware Test Dashboard")
    st.caption(
        "Monitor sensor measurements, warnings, faults, and health."
    )

    database_path = st.sidebar.text_input(
        "SQLite database",
        value="data/sensor_data.db",
    )

    readings = load_readings(database_path)
    frame = readings_to_dataframe(readings)

    if frame.empty:
        st.warning(
            "No sensor data was found. Run sensor-sim with "
            "--database before opening the dashboard."
        )
        return

    sensor_options = sorted(frame["sensor_id"].unique())
    status_options = sorted(frame["status"].unique())

    selected_sensors = st.sidebar.multiselect(
        "Sensors",
        options=sensor_options,
        default=sensor_options,
    )
    selected_statuses = st.sidebar.multiselect(
        "Statuses",
        options=status_options,
        default=status_options,
    )

    # Apply interactive filters before calculating the displayed metrics.
    filtered_frame = frame[
        frame["sensor_id"].isin(selected_sensors)
        & frame["status"].isin(selected_statuses)
    ]

    if filtered_frame.empty:
        st.warning("No readings match the selected filters.")
        return

    metrics = calculate_dashboard_metrics(filtered_frame)

    total_column, normal_column, warning_column, fault_column, score_column = (
        st.columns(5)
    )

    total_column.metric("Total readings", metrics["total"])
    normal_column.metric("Normal", metrics["normal"])
    warning_column.metric("Warnings", metrics["warning"])
    fault_column.metric("Faults", metrics["fault"])
    score_column.metric(
        "Health score",
        f'{metrics["health_score"]}%',
    )

    graph_column, status_column = st.columns([2, 1])

    with graph_column:
        st.plotly_chart(
            build_time_series_figure(filtered_frame),
            width="stretch",
        )

    with status_column:
        st.plotly_chart(
            build_status_figure(filtered_frame),
            width="stretch",
        )

    st.subheader("Latest Sensor Readings")
    st.dataframe(
        filtered_frame.sort_values(
            "timestamp",
            ascending=False,
        ),
        width="stretch",
        hide_index=True,
    )


if __name__ == "__main__":
    main()
