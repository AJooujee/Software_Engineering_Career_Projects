from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from observability_platform.db.base import Base


class MonitoredService(Base):
    __tablename__ = "monitored_services"
    __table_args__ = (
        UniqueConstraint(
            "name",
            "environment",
            name="uq_monitored_services_name_environment",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    name: Mapped[str] = mapped_column(String(100))
    environment: Mapped[str] = mapped_column(
        String(30),
        default="development",
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    telemetry_records: Mapped[list[TelemetryRecord]] = relationship(
        back_populates="service",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class TelemetryRecord(Base):
    __tablename__ = "telemetry_records"
    __table_args__ = (
        Index(
            "ix_telemetry_service_observed_at",
            "service_id",
            "observed_at",
        ),
        Index(
            "ix_telemetry_type_observed_at",
            "telemetry_type",
            "observed_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    service_id: Mapped[UUID] = mapped_column(
        ForeignKey("monitored_services.id", ondelete="CASCADE"),
    )
    telemetry_type: Mapped[str] = mapped_column(String(20))
    source: Mapped[str] = mapped_column(String(200), index=True)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)

    service: Mapped[MonitoredService] = relationship(
        back_populates="telemetry_records",
    )
