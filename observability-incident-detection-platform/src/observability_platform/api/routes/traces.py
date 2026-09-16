"""HTTP endpoints for distributed trace ingestion and retrieval."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from observability_platform.db.session import get_db_session
from observability_platform.schemas.trace import (
    TraceBatchCreate,
    TraceIngestResponse,
    TraceResponse,
)
from observability_platform.services.trace_ingestion_service import (
    DuplicateSpanError,
    MixedTraceBatchError,
    TraceIngestionService,
    UnregisteredTraceServiceError,
)
from observability_platform.services.trace_query_service import (
    TraceNotFoundError,
    TraceQueryService,
)

# Group trace operations under one versioned API prefix and Swagger tag.
router = APIRouter(
    prefix="/api/v1/traces",
    tags=["Distributed Tracing"],
)

# Inject one asynchronous database session into each endpoint request.
SessionDependency = Annotated[AsyncSession, Depends(get_db_session)]


@router.post(
    "",
    response_model=TraceIngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest a batch of distributed trace spans",
)
async def ingest_trace(
    batch: TraceBatchCreate,
    session: SessionDependency,
) -> TraceIngestResponse:
    """Validate and persist one batch of distributed trace spans."""

    # Construct the application service with the request-scoped session so all
    # duplicate checks, service lookups, and inserts share one transaction.
    trace_service = TraceIngestionService(session)

    try:
        # Delegate business validation and persistence to the service layer.
        return await trace_service.ingest(batch)
    except DuplicateSpanError as error:
        # A duplicate trace/span identity conflicts with an existing resource,
        # so expose the domain failure as HTTP 409.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    except (
        MixedTraceBatchError,
        UnregisteredTraceServiceError,
    ) as error:
        # These requests pass schema validation but violate trace ingestion
        # rules, so expose them as HTTP 422.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error


@router.get(
    "/{trace_id}",
    response_model=TraceResponse,
    summary="Get a distributed trace by trace ID",
)
async def get_trace(
    trace_id: Annotated[
        str,
        Path(
            # Validate the W3C trace identifier before querying the database.
            min_length=32,
            max_length=32,
            pattern=r"^[0-9a-f]{32}$",
        ),
    ],
    session: SessionDependency,
) -> TraceResponse:
    """Retrieve and reconstruct a distributed trace by its W3C trace ID."""

    # Keep ORM queries and response reconstruction outside the route handler.
    trace_service = TraceQueryService(session)

    try:
        # Return the complete trace with summary timing and ordered spans.
        return await trace_service.get_by_trace_id(trace_id)
    except TraceNotFoundError as error:
        # A valid identifier with no persistent spans represents a missing
        # trace resource.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
