from fastapi import APIRouter, status

from observability_platform.schemas.telemetry import (
    TelemetryBatch,
    TelemetryIngestResponse,
)
from observability_platform.services.telemetry_service import telemetry_store

router = APIRouter(
    prefix="/api/v1/telemetry",
    tags=["Telemetry"],
)


@router.post(
    "",
    response_model=TelemetryIngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest a batch of telemetry",
)
async def ingest_telemetry(
    batch: TelemetryBatch,
) -> TelemetryIngestResponse:
    return await telemetry_store.ingest(batch)
