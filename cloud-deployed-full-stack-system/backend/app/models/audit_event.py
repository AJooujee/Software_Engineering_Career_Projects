"""Immutable SQLAlchemy model for security-conscious audit history."""

from datetime import datetime, timezone
from enum import Enum as PythonEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.user import UserRole


class AuditAction(str, PythonEnum):
    """Define successful business mutations recorded by the platform."""

    INCIDENT_CREATED = "incident.created"
    INCIDENT_UPDATED = "incident.updated"
    INCIDENT_DELETED = "incident.deleted"
    USER_ROLE_CHANGED = "user.role_changed"
    USER_STATUS_CHANGED = "user.status_changed"


class AuditResourceType(str, PythonEnum):
    """Define resource categories referenced by audit events."""

    INCIDENT = "incident"
    USER = "user"


class AuditEvent(Base):
    """Persist an immutable snapshot of one successful mutation."""

    __tablename__ = "audit_events"

    # Explicit checks keep PostgreSQL and SQLite behavior aligned.
    __table_args__ = (
        CheckConstraint(
            "actor_role IN ('viewer', 'operator', 'admin')",
            name="audit_actor_role",
        ),
        CheckConstraint(
            (
                "action IN ("
                "'incident.created', "
                "'incident.updated', "
                "'incident.deleted', "
                "'user.role_changed', "
                "'user.status_changed'"
                ")"
            ),
            name="audit_action",
        ),
        CheckConstraint(
            "resource_type IN ('incident', 'user')",
            name="audit_resource_type",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Retain both the actor identifier and display snapshots so historical
    # entries remain understandable after future profile changes.
    actor_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    actor_email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
    )

    actor_role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            name="audit_actor_role",
            native_enum=False,
            create_constraint=False,
            values_callable=lambda enum_class: [
                member.value
                for member in enum_class
            ],
        ),
        nullable=False,
    )

    action: Mapped[AuditAction] = mapped_column(
        Enum(
            AuditAction,
            name="audit_action",
            native_enum=False,
            create_constraint=False,
            values_callable=lambda enum_class: [
                member.value
                for member in enum_class
            ],
        ),
        nullable=False,
        index=True,
    )

    resource_type: Mapped[AuditResourceType] = mapped_column(
        Enum(
            AuditResourceType,
            name="audit_resource_type",
            native_enum=False,
            create_constraint=False,
            values_callable=lambda enum_class: [
                member.value
                for member in enum_class
            ],
        ),
        nullable=False,
        index=True,
    )

    # Resource identifiers deliberately have no foreign key because audit
    # history must survive deletion of the referenced Incident.
    resource_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
        index=True,
    )

    resource_label: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
    )

    changes: Mapped[dict[str, object]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        index=True,
    )
