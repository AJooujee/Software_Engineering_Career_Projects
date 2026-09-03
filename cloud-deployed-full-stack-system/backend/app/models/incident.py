"""SQLAlchemy model and domain enums for operational incidents."""

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IncidentStatus(str, Enum):
    """Supported lifecycle states for an operational incident."""

    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentSeverity(str, Enum):
    """Supported business-impact levels for an incident."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Incident(Base):
    """Persist an operational incident reported by the platform."""

    __tablename__ = "incidents"

    # Declare enum checks explicitly so Alembic can compare model metadata
    # with the constraints already stored in PostgreSQL.
    __table_args__ = (
        CheckConstraint(
            "severity IN ('low', 'medium', 'high', 'critical')",
            name="incident_severity",
        ),
        CheckConstraint(
            "status IN ('open', 'investigating', 'resolved', 'closed')",
            name="incident_status",
        ),
    )

    # UUIDs remain unique across local, test, and cloud environments.
    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    service_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        index=True,
    )

    severity: Mapped[IncidentSeverity] = mapped_column(
        SqlEnum(
            IncidentSeverity,
            name="incident_severity",
            native_enum=False,
            create_constraint=False,
            values_callable=lambda enum_class: [
                member.value for member in enum_class
            ],
        ),
        nullable=False,
        default=IncidentSeverity.MEDIUM,
        server_default=IncidentSeverity.MEDIUM.value,
    )

    status: Mapped[IncidentStatus] = mapped_column(
        SqlEnum(
            IncidentStatus,
            name="incident_status",
            native_enum=False,
            create_constraint=False,
            values_callable=lambda enum_class: [
                member.value for member in enum_class
            ],
        ),
        nullable=False,
        default=IncidentStatus.OPEN,
        server_default=IncidentStatus.OPEN.value,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=func.now(),
    )
