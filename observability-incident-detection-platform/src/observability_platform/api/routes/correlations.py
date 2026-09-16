from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from observability_platform.db.session import get_db_session
from observability_platform.schemas.correlation import (
    CorrelationAnalyzeRequest,
    CorrelationQueryResponse,
    CorrelationResponse,
    CorrelationStatus,
)
from observability_platform.schemas.service import ServiceEnvironment
from observability_platform.services.correlation_query_service import (
    CorrelationNotFoundError,
    CorrelationQueryService,
)
from observability_platform.services.correlation_service import (
    CorrelationService,
    InsufficientIncidentsError,
)

router = APIRouter(
    prefix="/api/v1/correlations",
    tags=["Correlations"],
)

SessionDependency = Annotated[AsyncSession, Depends(get_db_session)]


@router.post(
    "/analyze",
    response_model=CorrelationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Correlate incidents and identify a probable root cause",
)
async def analyze_incidents(
    request: CorrelationAnalyzeRequest,
    session: SessionDependency,
) -> CorrelationResponse:
    correlation_service = CorrelationService(session)

    try:
        return await correlation_service.analyze(request)
    except InsufficientIncidentsError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error


@router.get(
    "",
    response_model=CorrelationQueryResponse,
    summary="Query correlations",
)
async def query_correlations(
    session: SessionDependency,
    service: Annotated[
        str | None,
        Query(min_length=1, max_length=100),
    ] = None,
    environment: ServiceEnvironment | None = None,
    correlation_status: Annotated[
        CorrelationStatus | None,
        Query(alias="status"),
    ] = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> CorrelationQueryResponse:
    query_service = CorrelationQueryService(session)

    return await query_service.query(
        service=service,
        environment=environment.value if environment is not None else None,
        status=(correlation_status.value if correlation_status is not None else None),
        created_from=created_from,
        created_to=created_to,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{correlation_id}",
    response_model=CorrelationResponse,
    summary="Get a correlation by ID",
)
async def get_correlation(
    correlation_id: UUID,
    session: SessionDependency,
) -> CorrelationResponse:
    query_service = CorrelationQueryService(session)

    try:
        return await query_service.get_by_id(correlation_id)
    except CorrelationNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
