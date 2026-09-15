from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from observability_platform.db.session import get_db_session
from observability_platform.schemas.anomaly import (
    AnomalyCategory,
    AnomalyQueryResponse,
    AnomalySeverity,
)
from observability_platform.schemas.service import ServiceEnvironment
from observability_platform.services.anomaly_query_service import (
    AnomalyQueryService,
    InvalidAnomalyTimeRangeError,
)

router = APIRouter(
    prefix="/api/v1/anomalies",
    tags=["Anomalies"],
)

SessionDependency = Annotated[AsyncSession, Depends(get_db_session)]


@router.get(
    "",
    response_model=AnomalyQueryResponse,
    summary="Query detected anomalies",
)
async def query_anomalies(
    session: SessionDependency,
    service: Annotated[
        str | None,
        Query(min_length=1, max_length=100),
    ] = None,
    environment: ServiceEnvironment | None = None,
    category: AnomalyCategory | None = None,
    severity: AnomalySeverity | None = None,
    rule_id: Annotated[
        str | None,
        Query(min_length=1, max_length=100),
    ] = None,
    detected_from: datetime | None = None,
    detected_to: datetime | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AnomalyQueryResponse:
    query_service = AnomalyQueryService(session)

    try:
        return await query_service.query(
            service=service,
            environment=environment,
            category=category,
            severity=severity,
            rule_id=rule_id,
            detected_from=detected_from,
            detected_to=detected_to,
            limit=limit,
            offset=offset,
        )
    except InvalidAnomalyTimeRangeError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
