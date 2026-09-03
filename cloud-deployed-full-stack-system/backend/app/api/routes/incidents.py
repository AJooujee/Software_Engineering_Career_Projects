"""FastAPI route handlers for operational incident management."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.incident import (
    IncidentCreate,
    IncidentResponse,
    IncidentUpdate,
)
import app.services.incidents as incident_service


# Group every incident endpoint under one router and Swagger tag.
router = APIRouter(
    prefix="/incidents",
    tags=["incidents"],
)

# Reuse the database dependency annotation across route handlers.
DatabaseSession = Annotated[Session, Depends(get_db)]


def incident_not_found_response(
    error: incident_service.IncidentNotFoundError,
) -> HTTPException:
    """Convert a service-level not-found error into an HTTP response."""

    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=str(error),
    )


@router.post(
    "",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an incident",
)
def create_incident(
    incident_data: IncidentCreate,
    database_session: DatabaseSession,
) -> IncidentResponse:
    """Create and return a new operational incident."""

    return incident_service.create_incident(
        database_session,
        incident_data,
    )


@router.get(
    "",
    response_model=list[IncidentResponse],
    summary="List incidents",
)
def list_incidents(
    database_session: DatabaseSession,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[IncidentResponse]:
    """Return a paginated collection of incidents."""

    return incident_service.list_incidents(
        database_session,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
    summary="Get an incident",
)
def get_incident(
    incident_id: UUID,
    database_session: DatabaseSession,
) -> IncidentResponse:
    """Return one incident by its identifier."""

    try:
        return incident_service.get_incident(
            database_session,
            incident_id,
        )
    except incident_service.IncidentNotFoundError as error:
        raise incident_not_found_response(error) from error


@router.patch(
    "/{incident_id}",
    response_model=IncidentResponse,
    summary="Update an incident",
)
def update_incident(
    incident_id: UUID,
    incident_data: IncidentUpdate,
    database_session: DatabaseSession,
) -> IncidentResponse:
    """Update selected fields on an existing incident."""

    try:
        return incident_service.update_incident(
            database_session,
            incident_id,
            incident_data,
        )
    except incident_service.IncidentNotFoundError as error:
        raise incident_not_found_response(error) from error


@router.delete(
    "/{incident_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an incident",
)
def delete_incident(
    incident_id: UUID,
    database_session: DatabaseSession,
) -> Response:
    """Delete an existing incident without returning a response body."""

    try:
        incident_service.delete_incident(
            database_session,
            incident_id,
        )
    except incident_service.IncidentNotFoundError as error:
        raise incident_not_found_response(error) from error

    return Response(status_code=status.HTTP_204_NO_CONTENT)
