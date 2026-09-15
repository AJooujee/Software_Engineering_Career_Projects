from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from observability_platform.db.session import get_db_session
from observability_platform.schemas.telemetry import (
    TelemetryBatch,
    TelemetryIngestResponse,
)
from observability_platform.services.persistent_telemetry_service import (
    PersistentTelemetryService,
    UnregisteredServiceError,
)

router = APIRouter(
    prefix="/api/v1/telemetry",
    tags=["Telemetry"],
)

SessionDependency = Annotated[AsyncSession, Depends(get_db_session)]


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
