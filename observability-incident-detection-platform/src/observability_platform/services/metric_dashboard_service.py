"""Application service for metric dashboard aggregation."""

from datetime import UTC, datetime, timedelta
from math import ceil

from sqlalchemy.ext.asyncio import AsyncSession

from observability_platform.repositories.telemetry_repository import (
    TelemetryRepository,
)
from observability_platform.schemas.dashboard import (
    MetricSummaryResponse,
    MetricTimeSeriesPoint,
)
from observability_platform.schemas.service import ServiceEnvironment


class MetricSamplesNotFoundError(Exception):
    """Raised when a dashboard query matches no metric samples."""


class InconsistentMetricUnitError(Exception):
    """Raised when matched samples use incompatible measurement units."""


class InvalidDashboardWindowError(Exception):
    """Raised when the dashboard time range is chronologically invalid."""


class MetricDashboardService:
    """Aggregate persistent metric telemetry into dashboard statistics."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize dashboard queries within the request database session."""

        # Reuse telemetry persistence instead of exposing ORM operations from
        # the dashboard service.
        self._telemetry_repository = TelemetryRepository(session)

    async def summarize(
        self,
        *,
        service: str,
        environment: ServiceEnvironment,
        metric_name: str,
        source: str | None = None,
        observed_from: datetime | None = None,
        observed_to: datetime | None = None,
        window_minutes: int = 60,
    ) -> MetricSummaryResponse:
        """Return statistics and chronological points for one metric."""

        # Use the current UTC time as the default upper boundary so requests
        # without explicit timestamps describe a recent operational window.
        window_ended_at = observed_to or datetime.now(UTC)

        # Derive the lower boundary from the requested window unless the caller
        # supplies an explicit starting timestamp.
        window_started_at = observed_from or (
            window_ended_at - timedelta(minutes=window_minutes)
        )

        # Reject reversed windows before issuing a database query.
        if window_started_at > window_ended_at:
            raise InvalidDashboardWindowError(
                "observed_from must be earlier than or equal to observed_to"
            )

        # Load only metric telemetry for the selected service, source, and
        # bounded time interval.
        rows = await self._telemetry_repository.query_metric_records(
            service=service,
            environment=environment.value,
            source=source,
            observed_from=window_started_at,
            observed_to=window_ended_at,
        )

        # Metric name remains in the portable JSON payload, so filter it after
        # shared column filters have reduced the candidate record set.
        matching_rows = [
            (record, monitored_service)
            for record, monitored_service in rows
            if record.payload.get("name") == metric_name
        ]

        # An empty result cannot produce meaningful numeric statistics.
        if not matching_rows:
            raise MetricSamplesNotFoundError(
                f"No samples found for metric '{metric_name}' on "
                f"service '{service}' in environment "
                f"'{environment.value}'"
            )

        # A dashboard series must use one measurement unit. Combining percent,
        # milliseconds, bytes, or other units would produce invalid statistics.
        units = {record.payload.get("unit") for record, _ in matching_rows}

        if len(units) > 1:
            raise InconsistentMetricUnitError(
                f"Metric '{metric_name}' contains inconsistent units"
            )

        # Convert validated numeric payload values into floats for consistent
        # aggregation and JSON response types.
        values = [float(record.payload["value"]) for record, _ in matching_rows]

        # Repository ordering is chronological, so the final record is the
        # newest observation represented by this dashboard response.
        latest_record = matching_rows[-1][0]

        # Sort a copy of values for percentile selection without changing the
        # chronological order used by time-series points.
        sorted_values = sorted(values)

        # Use the nearest-rank percentile method. At least one sample exists,
        # so the resulting zero-based index is always valid.
        p95_index = max(0, ceil(0.95 * len(sorted_values)) - 1)
        p95_value = sorted_values[p95_index]

        # Convert persistent records into lightweight chart points.
        points = [
            MetricTimeSeriesPoint(
                observed_at=record.observed_at,
                value=float(record.payload["value"]),
                source=record.source,
            )
            for record, _ in matching_rows
        ]

        # Return both statistical summary fields and the underlying ordered
        # points so clients can render status cards and trend charts together.
        return MetricSummaryResponse(
            service=service,
            environment=environment,
            metric_name=metric_name,
            unit=next(iter(units)),
            sources=sorted({record.source for record, _ in matching_rows}),
            # Report the actual sample interval rather than the wider requested
            # query window when no samples occur at its boundaries.
            window_started_at=matching_rows[0][0].observed_at,
            window_ended_at=latest_record.observed_at,
            sample_count=len(values),
            minimum_value=min(values),
            maximum_value=max(values),
            average_value=round(sum(values) / len(values), 3),
            p95_value=p95_value,
            latest_value=float(latest_record.payload["value"]),
            latest_observed_at=latest_record.observed_at,
            points=points,
        )
