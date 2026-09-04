"""FastAPI route handlers for operational incident management."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.api.dependencies import (
    CurrentUser,
    DatabaseSession,
    require_roles,
)
from app.models.user import User, UserRole
from app.schemas.incident import (
    IncidentCreate,
    IncidentResponse,
    IncidentUpdate,
)
import app.services.incidents as incident_service


router = APIRouter(
    prefix="/incidents",
    tags=["incidents"],
)

IncidentOperator = Annotated[
    User,
    Depends(
        require_roles(
            UserRole.OPERATOR,
            UserRole.ADMIN,
        )
    ),
]

IncidentAdministrator = Annotated[
    User,
    Depends(require_roles(UserRole.ADMIN)),
]


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
    authorized_user: IncidentOperator,
) -> IncidentResponse:
    """Create an incident when the user is an operator or administrator."""

    del authorized_user

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
    current_user: CurrentUser,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[IncidentResponse]:
    """Return incidents to any authenticated active user."""

    del current_user

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
    current_user: CurrentUser,
) -> IncidentResponse:
    """Return one incident to any authenticated active user."""

    del current_user

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
    authorized_user: IncidentOperator,
) -> IncidentResponse:
    """Update an incident as an operator or administrator."""

    del authorized_user

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
    administrator: IncidentAdministrator,
) -> Response:
    """Delete an incident when the current user is an administrator."""

    del administrator

    try:
        incident_service.delete_incident(
            database_session,
            incident_id,
        )
    except incident_service.IncidentNotFoundError as error:
        raise incident_not_found_response(error) from error

    return Response(status_code=status.HTTP_204_NO_CONTENT)
