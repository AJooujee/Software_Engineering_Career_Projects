from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from observability_platform.db.session import get_db_session
from observability_platform.schemas.service import ServiceEnvironment
from observability_platform.schemas.telemetry import (
    TelemetryBatch,
    TelemetryIngestResponse,
    TelemetryQueryResponse,
)
from observability_platform.services.persistent_telemetry_service import (
    PersistentTelemetryService,
    UnregisteredServiceError,
)
from observability_platform.services.telemetry_query_service import (
    InvalidTelemetryTimeRangeError,
    TelemetryQueryService,
)

router = APIRouter(
    prefix="/api/v1/telemetry",
    tags=["Telemetry"],
)

SessionDependency = Annotated[AsyncSession, Depends(get_db_session)]


@router.get(
    "",
    response_model=TelemetryQueryResponse,
    summary="Query stored telemetry",
)
async def query_telemetry(
    session: SessionDependency,
    service: Annotated[
        str | None,
        Query(min_length=1, max_length=100),
    ] = None,
    environment: ServiceEnvironment | None = None,
    telemetry_type: Annotated[
        Literal["metric", "log", "event"] | None,
        Query(alias="type"),
    ] = None,
    source: Annotated[
        str | None,
        Query(min_length=1, max_length=200),
    ] = None,
    observed_from: datetime | None = None,
    observed_to: datetime | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TelemetryQueryResponse:
    query_service = TelemetryQueryService(session)

    try:
        return await query_service.query(
            service=service,
            environment=environment,
            telemetry_type=telemetry_type,
            source=source,
            observed_from=observed_from,
            observed_to=observed_to,
            limit=limit,
            offset=offset,
        )
    except InvalidTelemetryTimeRangeError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error


@router.post(
    "",
    response_model=TelemetryIngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest a batch of telemetry",
)
async def ingest_telemetry(
    batch: TelemetryBatch,
    session: SessionDependency,
) -> TelemetryIngestResponse:
    telemetry_service = PersistentTelemetryService(session)

    try:
        return await telemetry_service.ingest(batch)
    except UnregisteredServiceError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
