from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from observability_platform.db.session import get_db_session
from observability_platform.schemas.incident import (
    IncidentAcknowledgeRequest,
    IncidentQueryResponse,
    IncidentResolveRequest,
    IncidentResponse,
    IncidentSeverity,
    IncidentStatus,
)
from observability_platform.schemas.service import ServiceEnvironment
from observability_platform.services.incident_service import (
    IncidentNotFoundError,
    IncidentService,
    InvalidIncidentTimeRangeError,
    InvalidIncidentTransitionError,
)

router = APIRouter(
    prefix="/api/v1/incidents",
    tags=["Incidents"],
)

SessionDependency = Annotated[AsyncSession, Depends(get_db_session)]


@router.get(
    "",
    response_model=IncidentQueryResponse,
    summary="Query incidents",
)
async def query_incidents(
    session: SessionDependency,
    service: Annotated[
        str | None,
        Query(min_length=1, max_length=100),
    ] = None,
    environment: ServiceEnvironment | None = None,
    incident_status: Annotated[
        IncidentStatus | None,
        Query(alias="status"),
    ] = None,
    severity: IncidentSeverity | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> IncidentQueryResponse:
    incident_service = IncidentService(session)

    try:
        return await incident_service.query(
            service=service,
            environment=environment,
            status=incident_status,
            severity=severity,
            created_from=created_from,
            created_to=created_to,
            limit=limit,
            offset=offset,
        )
    except InvalidIncidentTimeRangeError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
    summary="Get an incident",
)
async def get_incident(
    incident_id: UUID,
    session: SessionDependency,
) -> IncidentResponse:
    incident_service = IncidentService(session)

    try:
        return await incident_service.get(incident_id)
    except IncidentNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@router.patch(
    "/{incident_id}/acknowledge",
    response_model=IncidentResponse,
    summary="Acknowledge an incident",
)
async def acknowledge_incident(
    incident_id: UUID,
    request: IncidentAcknowledgeRequest,
    session: SessionDependency,
) -> IncidentResponse:
    incident_service = IncidentService(session)

    try:
        return await incident_service.acknowledge(
            incident_id,
            acknowledged_by=request.acknowledged_by,
        )
    except IncidentNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except InvalidIncidentTransitionError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


@router.patch(
    "/{incident_id}/resolve",
    response_model=IncidentResponse,
    summary="Resolve an incident",
)
async def resolve_incident(
    incident_id: UUID,
    request: IncidentResolveRequest,
    session: SessionDependency,
) -> IncidentResponse:
    incident_service = IncidentService(session)

    try:
        return await incident_service.resolve(
            incident_id,
            resolved_by=request.resolved_by,
            resolution_summary=request.resolution_summary,
        )
    except IncidentNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except InvalidIncidentTransitionError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
