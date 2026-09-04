"""Administrator API routes for user and role management."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import DatabaseSession, require_roles
from app.models.user import User, UserRole
from app.schemas.user import (
    UserResponse,
    UserRoleUpdate,
    UserStatusUpdate,
)
import app.services.auth as auth_service


router = APIRouter(
    prefix="/users",
    tags=["users"],
)

Administrator = Annotated[
    User,
    Depends(require_roles(UserRole.ADMIN)),
]


def user_not_found_response(
    error: auth_service.UserNotFoundError,
) -> HTTPException:
    """Convert a service-level user error into an HTTP response."""

    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=str(error),
    )


@router.get(
    "",
    response_model=list[UserResponse],
    summary="List registered users",
)
def list_users(
    database_session: DatabaseSession,
    administrator: Administrator,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[UserResponse]:
    """Return registered users to an administrator."""

    del administrator

    return auth_service.list_registered_users(
        database_session,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get a registered user",
)
def get_user(
    user_id: UUID,
    database_session: DatabaseSession,
    administrator: Administrator,
) -> UserResponse:
    """Return one registered user to an administrator."""

    del administrator

    try:
        return auth_service.get_user(
            database_session,
            user_id,
        )
    except auth_service.UserNotFoundError as error:
        raise user_not_found_response(error) from error


@router.patch(
    "/{user_id}/role",
    response_model=UserResponse,
    summary="Change a user's role",
)
def update_user_role(
    user_id: UUID,
    user_data: UserRoleUpdate,
    database_session: DatabaseSession,
    administrator: Administrator,
) -> UserResponse:
    """Change a user's role while preventing accidental self-demotion."""

    if (
        user_id == administrator.id
        and user_data.role != UserRole.ADMIN
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot remove their own admin role.",
        )

    try:
        return auth_service.change_user_role(
            database_session,
            user_id,
            user_data.role,
        )
    except auth_service.UserNotFoundError as error:
        raise user_not_found_response(error) from error


@router.patch(
    "/{user_id}/status",
    response_model=UserResponse,
    summary="Change a user's account status",
)
def update_user_status(
    user_id: UUID,
    user_data: UserStatusUpdate,
    database_session: DatabaseSession,
    administrator: Administrator,
) -> UserResponse:
    """Activate or disable a user while preventing self-deactivation."""

    if (
        user_id == administrator.id
        and not user_data.is_active
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot disable their own account.",
        )

    try:
        return auth_service.change_user_status(
            database_session,
            user_id,
            is_active=user_data.is_active,
        )
    except auth_service.UserNotFoundError as error:
        raise user_not_found_response(error) from error
