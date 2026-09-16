"""Database operations for persistent distributed trace spans."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from observability_platform.db.models import (
    MonitoredService,
    TraceSpanRecord,
)
from observability_platform.schemas.trace import TraceSpanCreate

# Return the span and its resolved service together so upper layers do not
# issue a separate service query for every span.
TraceSpanRow = tuple[TraceSpanRecord, MonitoredService]


class TraceRepository:
    """Persist trace spans and retrieve complete distributed traces."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind repository operations to the caller's database transaction."""

        # The service layer owns commit and rollback decisions.
        self._session = session

    async def create_batch(
        self,
        spans: list[tuple[TraceSpanCreate, UUID]],
        *,
        received_at: datetime,
    ) -> list[TraceSpanRecord]:
        """Build and flush persistent records for a validated span batch."""

        # Build every record before flushing so the batch participates in one
        # caller-controlled transaction.
        records = []

        for span, service_id in spans:
            # Persist duration separately to support efficient latency
            # aggregation without recalculating timestamp differences.
            duration_ms = (span.ended_at - span.started_at).total_seconds() * 1000

            # Generate an internal UUID while preserving the external W3C trace
            # and span identifiers used by instrumentation clients.
            record = TraceSpanRecord(
                id=uuid4(),
                service_id=service_id,
                trace_id=span.trace_id,
                span_id=span.span_id,
                parent_span_id=span.parent_span_id,
                source=span.source,
                operation=span.operation,
                status=span.status.value,
                started_at=span.started_at,
                ended_at=span.ended_at,
                duration_ms=round(duration_ms, 3),
                attributes=span.attributes,
                received_at=received_at,
            )
            records.append(record)

        # Flush assigns database state and exposes constraint failures while
        # leaving commit or rollback under service-layer control.
        self._session.add_all(records)
        await self._session.flush()

        return records

    async def get_by_trace_id(
        self,
        trace_id: str,
    ) -> list[TraceSpanRow]:
        """Load every span and service participating in one trace."""

        # Join the service table once so response mapping does not produce an
        # N+1 query for a trace containing many spans.
        statement = (
            select(TraceSpanRecord, MonitoredService)
            .select_from(TraceSpanRecord)
            .join(
                MonitoredService,
                MonitoredService.id == TraceSpanRecord.service_id,
            )
            .where(TraceSpanRecord.trace_id == trace_id)
            .order_by(
                # Chronological order makes the reconstructed trace stable and
                # easier for API clients to display as a timeline.
                TraceSpanRecord.started_at,
                TraceSpanRecord.span_id,
            )
        )
        result = await self._session.execute(statement)

        # Materialize rows before returning so repository consumers receive a
        # predictable list instead of a live SQLAlchemy result object.
        return [(span, service) for span, service in result.all()]

    async def find_existing_span_ids(
        self,
        trace_id: str,
        span_ids: set[str],
    ) -> set[str]:
        """Return requested span IDs already stored under the trace ID."""

        # Avoid generating an unnecessary or database-specific empty IN query.
        if not span_ids:
            return set()

        # Read only identity values because full ORM records are unnecessary
        # for duplicate detection.
        statement = select(TraceSpanRecord.span_id).where(
            TraceSpanRecord.trace_id == trace_id,
            TraceSpanRecord.span_id.in_(span_ids),
        )
        result = await self._session.execute(statement)

        # A set supports efficient comparison and provides unique values to the
        # ingestion service for a clear conflict response.
        return set(result.scalars().all())
