"""Application service for reconstructing distributed trace responses."""

from sqlalchemy.ext.asyncio import AsyncSession

from observability_platform.repositories.trace_repository import (
    TraceRepository,
)
from observability_platform.schemas.trace import (
    TraceResponse,
    TraceSpanResponse,
)


class TraceNotFoundError(Exception):
    """Raised when no persistent spans exist for a requested trace ID."""


class TraceQueryService:
    """Load persistent spans and reconstruct a complete distributed trace."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize trace queries within the request database session."""

        # Query operations remain isolated behind the repository layer.
        self._trace_repository = TraceRepository(session)

    async def get_by_trace_id(
        self,
        trace_id: str,
    ) -> TraceResponse:
        """Return one distributed trace assembled from its persistent spans."""

        # Load spans with their monitored services in chronological order.
        rows = await self._trace_repository.get_by_trace_id(trace_id)

        # An empty result indicates that the trace resource does not exist.
        if not rows:
            raise TraceNotFoundError(f"Trace '{trace_id}' was not found")

        # A distributed request may cross multiple services. A set removes
        # duplicates, while sorting keeps the API response deterministic.
        services = sorted({service.name for _, service in rows})

        # The complete trace begins with its earliest span and ends with its
        # latest finishing span, even when spans overlap or run concurrently.
        started_at = min(span.started_at for span, _ in rows)
        ended_at = max(span.ended_at for span, _ in rows)

        # Use wall-clock duration instead of summing individual span durations.
        # Summation would double-count time when parent and child spans overlap.
        duration_ms = (ended_at - started_at).total_seconds() * 1000

        # Convert ORM rows to transport schemas so database implementation
        # details do not escape through the API layer.
        spans = [
            TraceSpanResponse(
                # Preserve both the internal database ID and external trace
                # identifiers for persistence and instrumentation debugging.
                id=span.id,
                trace_id=span.trace_id,
                span_id=span.span_id,
                parent_span_id=span.parent_span_id,
                # Include resolved service identity for multi-service displays.
                service_id=service.id,
                service=service.name,
                environment=service.environment,
                source=span.source,
                # Return execution details and timing information.
                operation=span.operation,
                status=span.status,
                started_at=span.started_at,
                ended_at=span.ended_at,
                duration_ms=span.duration_ms,
                # Preserve instrumentation metadata supplied during ingestion.
                attributes=span.attributes,
            )
            for span, service in rows
        ]

        # Return one summary object containing the trace-level interval,
        # participating services, and chronologically ordered spans.
        return TraceResponse(
            trace_id=trace_id,
            span_count=len(spans),
            started_at=started_at,
            ended_at=ended_at,
            duration_ms=round(duration_ms, 3),
            services=services,
            spans=spans,
        )
