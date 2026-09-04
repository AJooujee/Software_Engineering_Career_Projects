"""Database access operations for application users."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User, UserRole


def get_user_by_id(
    database_session: Session,
    user_id: UUID,
) -> User | None:
    """Return one user by identifier when the record exists."""

    return database_session.get(User, user_id)


def get_user_by_email(
    database_session: Session,
    email: str,
) -> User | None:
    """Return one user by normalized email address."""

    normalized_email = email.strip().lower()

    statement = select(User).where(
        User.email == normalized_email,
    )

    return database_session.scalar(statement)


def list_users(
    database_session: Session,
    *,
    offset: int = 0,
    limit: int = 100,
) -> list[User]:
    """Return users ordered by their creation time."""

    statement = (
        select(User)
        .order_by(User.created_at.asc())
        .offset(offset)
        .limit(limit)
    )

    return list(database_session.scalars(statement).all())


def create_user(
    database_session: Session,
    *,
    email: str,
    full_name: str,
    password_hash: str,
    role: UserRole = UserRole.VIEWER,
) -> User:
    """Stage a user containing only a password hash."""

    user = User(
        email=email.strip().lower(),
        full_name=full_name.strip(),
        password_hash=password_hash,
        role=role,
    )

    database_session.add(user)
    database_session.flush()
    database_session.refresh(user)

    return user


def update_user_role(
    database_session: Session,
    user: User,
    role: UserRole,
) -> User:
    """Stage a new authorization role for an existing user."""

    user.role = role

    database_session.add(user)
    database_session.flush()
    database_session.refresh(user)

    return user


def update_user_status(
    database_session: Session,
    user: User,
    *,
    is_active: bool,
) -> User:
    """Stage an active or disabled status for an existing user."""

    user.is_active = is_active

    database_session.add(user)
    database_session.flush()
    database_session.refresh(user)

    return user
