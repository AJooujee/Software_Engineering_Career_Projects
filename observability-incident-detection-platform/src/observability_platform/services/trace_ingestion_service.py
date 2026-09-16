"""Application service for validating and ingesting trace span batches."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from observability_platform.repositories.service_repository import (
    ServiceRepository,
)
from observability_platform.repositories.trace_repository import (
    TraceRepository,
)
from observability_platform.schemas.service import ServiceEnvironment
from observability_platform.schemas.trace import (
    TraceBatchCreate,
    TraceIngestResponse,
    TraceSpanCreate,
)


class MixedTraceBatchError(Exception):
    """Raised when one ingestion batch contains multiple trace IDs."""


class DuplicateSpanError(Exception):
    """Raised when a trace contains a repeated span identity."""


class UnregisteredTraceServiceError(Exception):
    """Raised when a span references a service absent from the registry."""


class TraceIngestionService:
    """Validate and persist one distributed trace batch atomically."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repositories that share one database transaction."""

        # All repositories receive the same session so service resolution,
        # duplicate checks, and span inserts use one transactional context.
        self._session = session
        self._service_repository = ServiceRepository(session)
        self._trace_repository = TraceRepository(session)

    async def ingest(
        self,
        batch: TraceBatchCreate,
    ) -> TraceIngestResponse:
        """Validate, resolve, and persist all spans in one batch."""

        # One batch represents one distributed trace. Keeping trace identity
        # consistent makes duplicate validation and transaction behavior clear.
        trace_ids = {span.trace_id for span in batch.spans}

        if len(trace_ids) != 1:
            raise MixedTraceBatchError(
                "All spans in a batch must share the same trace_id"
            )

        # The set has exactly one item after mixed-trace validation succeeds.
        trace_id = next(iter(trace_ids))

        # Preserve the original list length so duplicate values inside the
        # request can be detected before any database operation.
        span_ids = [span.span_id for span in batch.spans]

        if len(span_ids) != len(set(span_ids)):
            raise DuplicateSpanError(f"Trace '{trace_id}' contains duplicate span_ids")

        # Check persistent identities separately from request-local duplicates.
        # This prevents replaying spans already accepted for the same trace.
        existing_span_ids = await self._trace_repository.find_existing_span_ids(
            trace_id,
            set(span_ids),
        )

        if existing_span_ids:
            # Sort identifiers so the error message remains deterministic.
            duplicate_ids = ", ".join(sorted(existing_span_ids))

            raise DuplicateSpanError(
                f"Trace '{trace_id}' already contains span_ids: {duplicate_ids}"
            )

        # Resolve external service names and environments to database UUIDs
        # before constructing persistent span records.
        resolved_spans = await self._resolve_services(batch.spans)

        # Apply one receive time to all records accepted in this transaction.
        received_at = datetime.now(UTC)

        try:
            # Flush and commit the complete batch together. If any constraint
            # fails, no partial distributed trace remains in the database.
            records = await self._trace_repository.create_batch(
                resolved_spans,
                received_at=received_at,
            )
            await self._session.commit()
        except Exception:
            # Restore the session and database to their pre-request state
            # before propagating the original exception.
            await self._session.rollback()
            raise

        # Return internal record IDs so clients can reconcile accepted spans
        # without exposing database operations inside the repository.
        return TraceIngestResponse(
            accepted_count=len(records),
            span_record_ids=[record.id for record in records],
            received_at=received_at,
        )

    async def _resolve_services(
        self,
        spans: list[TraceSpanCreate],
    ) -> list[tuple[TraceSpanCreate, UUID]]:
        """Resolve each span's service identity to a persistent UUID."""

        # Cache identities because many spans commonly originate from the same
        # service and environment within one distributed trace.
        service_ids: dict[tuple[str, ServiceEnvironment], UUID] = {}

        # Preserve each validated span alongside its resolved foreign key for
        # repository batch creation.
        resolved_spans = []

        for span in spans:
            identity = (span.service, span.environment)
            service_id = service_ids.get(identity)

            # Query the service registry only once for each unique identity.
            if service_id is None:
                service = await self._service_repository.get_by_identity(
                    span.service,
                    span.environment,
                )

                # Trace data from unknown services cannot satisfy the required
                # foreign key or platform ownership model.
                if service is None:
                    raise UnregisteredTraceServiceError(
                        f"Service '{span.service}' is not registered "
                        f"in environment '{span.environment.value}'"
                    )

                # Cache the UUID for later spans from the same service.
                service_id = service.id
                service_ids[identity] = service_id

            resolved_spans.append((span, service_id))

        return resolved_spans
