"""Database access operations for immutable audit history."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_event import (
    AuditAction,
    AuditEvent,
    AuditResourceType,
)
from app.models.user import User, UserRole


def create_audit_event(
    database_session: Session,
    *,
    actor: User,
    action: AuditAction,
    resource_type: AuditResourceType,
    resource_id: UUID,
    resource_label: str,
    changes: dict[str, dict[str, object]],
) -> AuditEvent:
    """Stage an audit event inside the caller's database transaction."""

    event = AuditEvent(
        actor_user_id=actor.id,
        actor_email=actor.email,
        actor_role=UserRole(actor.role),
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_label=resource_label,
        changes=changes,
    )

    database_session.add(event)
    database_session.flush()
    database_session.refresh(event)

    return event


def list_audit_events(
    database_session: Session,
    *,
    offset: int = 0,
    limit: int = 50,
) -> list[AuditEvent]:
    """Return immutable audit events ordered from newest to oldest."""

    statement = (
        select(AuditEvent)
        .order_by(
            AuditEvent.created_at.desc(),
            AuditEvent.id.desc(),
        )
        .offset(offset)
        .limit(limit)
    )

    return list(database_session.scalars(statement).all())
