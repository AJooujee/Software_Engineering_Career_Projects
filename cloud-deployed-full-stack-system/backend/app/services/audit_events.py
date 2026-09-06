"""Business helpers for recording and reading audit history."""

from enum import Enum
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit_event import (
    AuditAction,
    AuditEvent,
    AuditResourceType,
)
from app.models.user import User
import app.repositories.audit_events as audit_repository


def normalize_audit_value(value: object) -> object:
    """Convert domain values into JSON-safe audit representations."""

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, UUID):
        return str(value)

    return value


def build_change_set(
    previous_values: dict[str, object],
    current_values: dict[str, object],
) -> dict[str, dict[str, object]]:
    """Return only fields whose normalized values materially changed."""

    changes: dict[str, dict[str, object]] = {}

    for field_name, current_value in current_values.items():
        previous_value = previous_values.get(field_name)
        normalized_previous = normalize_audit_value(
            previous_value,
        )
        normalized_current = normalize_audit_value(
            current_value,
        )

        if normalized_previous == normalized_current:
            continue

        changes[field_name] = {
            "from": normalized_previous,
            "to": normalized_current,
        }

    return changes


def record_audit_event(
    database_session: Session,
    *,
    actor: User,
    action: AuditAction,
    resource_type: AuditResourceType,
    resource_id: UUID,
    resource_label: str,
    changes: dict[str, dict[str, object]],
) -> AuditEvent:
    """Stage an audit event without independently committing it."""

    # The owning business service commits the resource mutation and its
    # audit event atomically in one transaction.
    return audit_repository.create_audit_event(
        database_session,
        actor=actor,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_label=resource_label,
        changes=changes,
    )


def list_audit_events(
    database_session: Session,
    *,
    offset: int = 0,
    limit: int = 50,
) -> list[AuditEvent]:
    """Return paginated audit history without changing transaction state."""

    return audit_repository.list_audit_events(
        database_session,
        offset=offset,
        limit=limit,
    )
