"""Authentication and user-management business services."""

from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User, UserRole
import app.repositories.users as user_repository
from app.schemas.user import UserCreate


class EmailAlreadyRegisteredError(ValueError):
    """Raised when registration uses an existing email address."""

    def __init__(self, email: str) -> None:
        super().__init__(f"Email '{email}' is already registered.")


class InvalidCredentialsError(ValueError):
    """Raised when login credentials cannot be authenticated."""

    def __init__(self) -> None:
        super().__init__("Incorrect email or password.")


class InactiveUserError(PermissionError):
    """Raised when a disabled user attempts to authenticate."""

    def __init__(self) -> None:
        super().__init__("User account is disabled.")


class UserNotFoundError(LookupError):
    """Raised when a requested user record does not exist."""

    def __init__(self, user_id: UUID) -> None:
        super().__init__(f"User '{user_id}' was not found.")


# Perform password verification even when an email does not exist.
# This reduces observable timing differences during failed login attempts.
DUMMY_PASSWORD_HASH = hash_password(
    "CloudOperationsDummyPassword123!",
)


def register_user(
    database_session: Session,
    user_data: UserCreate,
) -> User:
    """Register and commit a viewer account with a hashed password."""

    normalized_email = str(user_data.email).strip().lower()

    existing_user = user_repository.get_user_by_email(
        database_session,
        normalized_email,
    )

    if existing_user is not None:
        raise EmailAlreadyRegisteredError(normalized_email)

    hashed_password = hash_password(user_data.password)

    try:
        user = user_repository.create_user(
            database_session,
            email=normalized_email,
            full_name=user_data.full_name,
            password_hash=hashed_password,
            role=UserRole.VIEWER,
        )
        database_session.commit()
        return user
    except IntegrityError as error:
        # Handle a concurrent registration that passed the initial lookup.
        database_session.rollback()
        raise EmailAlreadyRegisteredError(normalized_email) from error
    except Exception:
        database_session.rollback()
        raise


def authenticate_user(
    database_session: Session,
    *,
    email: str,
    password: str,
) -> User:
    """Authenticate an active user without revealing account existence."""

    user = user_repository.get_user_by_email(
        database_session,
        email,
    )

    stored_password_hash = (
        user.password_hash
        if user is not None
        else DUMMY_PASSWORD_HASH
    )

    password_is_valid = verify_password(
        password,
        stored_password_hash,
    )

    if user is None or not password_is_valid:
        raise InvalidCredentialsError()

    if not user.is_active:
        raise InactiveUserError()

    return user


def create_user_access_token(user: User) -> str:
    """Create an access token containing the user's database identifier."""

    return create_access_token(str(user.id))


def get_user(
    database_session: Session,
    user_id: UUID,
) -> User:
    """Return an existing user or raise a service-level error."""

    user = user_repository.get_user_by_id(
        database_session,
        user_id,
    )

    if user is None:
        raise UserNotFoundError(user_id)

    return user


def list_registered_users(
    database_session: Session,
    *,
    offset: int = 0,
    limit: int = 100,
) -> list[User]:
    """Return a paginated list of registered users."""

    return user_repository.list_users(
        database_session,
        offset=offset,
        limit=limit,
    )


def change_user_role(
    database_session: Session,
    user_id: UUID,
    role: UserRole,
) -> User:
    """Change and commit the authorization role assigned to one user."""

    user = get_user(database_session, user_id)

    try:
        updated_user = user_repository.update_user_role(
            database_session,
            user,
            role,
        )
        database_session.commit()
        return updated_user
    except Exception:
        database_session.rollback()
        raise


def change_user_status(
    database_session: Session,
    user_id: UUID,
    *,
    is_active: bool,
) -> User:
    """Activate or disable one user account and commit the change."""

    user = get_user(database_session, user_id)

    try:
        updated_user = user_repository.update_user_status(
            database_session,
            user,
            is_active=is_active,
        )
        database_session.commit()
        return updated_user
    except Exception:
        database_session.rollback()
        raise
