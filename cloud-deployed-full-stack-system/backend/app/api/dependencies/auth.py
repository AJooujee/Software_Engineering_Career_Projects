"""FastAPI dependencies for authentication and role authorization."""

from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User, UserRole
import app.services.auth as auth_service


# Tell Swagger where clients can exchange credentials for an access token.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/token",
)

DatabaseSession = Annotated[Session, Depends(get_db)]
AccessToken = Annotated[str, Depends(oauth2_scheme)]


def credentials_exception() -> HTTPException:
    """Return the standard response for an invalid access token."""

    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: AccessToken,
    database_session: DatabaseSession,
) -> User:
    """Validate a token and load the current user from the database."""

    try:
        subject = decode_access_token(token)
        user_id = UUID(subject)
        user = auth_service.get_user(
            database_session,
            user_id,
        )
    except (
        InvalidTokenError,
        ValueError,
        auth_service.UserNotFoundError,
    ) as error:
        raise credentials_exception() from error

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled.",
        )

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(
    *allowed_roles: UserRole,
) -> Callable[[User], User]:
    """Create a dependency that permits only selected user roles."""

    if not allowed_roles:
        raise ValueError("At least one allowed role is required.")

    def role_checker(
        current_user: CurrentUser,
    ) -> User:
        """Return the user when their current database role is allowed."""

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )

        return current_user

    return role_checker
