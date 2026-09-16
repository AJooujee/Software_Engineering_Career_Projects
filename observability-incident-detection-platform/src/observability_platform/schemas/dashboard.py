"""Pydantic response contracts for metric dashboard APIs."""

from datetime import datetime

from pydantic import BaseModel, Field

from observability_platform.schemas.service import ServiceEnvironment


class MetricTimeSeriesPoint(BaseModel):
    """Represent one observed metric value on a dashboard timeline."""

    # Preserve the telemetry observation time rather than database receipt
    # time so delayed ingestion does not distort the operational timeline.
    observed_at: datetime

    # Return a normalized floating-point value for charting and aggregation.
    value: float

    # Identify the runtime instance that emitted this metric point.
    source: str


class MetricSummaryResponse(BaseModel):
    """Represent aggregated statistics and time-series points for one metric."""

    # Identify the monitored service and environment selected by the query.
    service: str
    environment: ServiceEnvironment

    # Identify the metric and optional measurement unit stored in telemetry.
    metric_name: str
    unit: str | None

    # Report every source represented in the aggregation exactly once.
    sources: list[str]

    # Describe the actual observation interval covered by returned samples.
    window_started_at: datetime
    window_ended_at: datetime

    # Count must be positive because an empty query returns a not-found error.
    sample_count: int = Field(ge=1)

    # Provide common dashboard statistics calculated from all matched samples.
    minimum_value: float
    maximum_value: float
    average_value: float
    p95_value: float

    # Surface the newest observation for operational status displays.
    latest_value: float
    latest_observed_at: datetime

    # Return chronological points so clients can render a metric trend chart.
    points: list[MetricTimeSeriesPoint]
