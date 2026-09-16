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
    incidents: Mapped[list[IncidentRecord]] = relationship(
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

    anomalies: Mapped[list[AnomalyRecord]] = relationship(
        back_populates="telemetry",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class AnomalyRecord(Base):
    __tablename__ = "anomaly_records"
    __table_args__ = (
        Index(
            "ix_anomaly_severity_detected_at",
            "severity",
            "detected_at",
        ),
        Index(
            "ix_anomaly_rule_detected_at",
            "rule_id",
            "detected_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    telemetry_id: Mapped[UUID] = mapped_column(
        ForeignKey("telemetry_records.id", ondelete="CASCADE"),
        index=True,
    )
    rule_id: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(30))
    severity: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    observed_value: Mapped[str | float] = mapped_column(JSON)
    threshold: Mapped[str | float | None] = mapped_column(
        JSON,
        nullable=True,
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    telemetry: Mapped[TelemetryRecord] = relationship(
        back_populates="anomalies",
    )
    incident: Mapped[IncidentRecord | None] = relationship(
        back_populates="trigger_anomaly",
        uselist=False,
    )


class IncidentRecord(Base):
    __tablename__ = "incidents"
    __table_args__ = (
        UniqueConstraint(
            "trigger_anomaly_id",
            name="uq_incidents_trigger_anomaly_id",
        ),
        Index(
            "ix_incident_status_created_at",
            "status",
            "created_at",
        ),
        Index(
            "ix_incident_severity_created_at",
            "severity",
            "created_at",
        ),
        Index(
            "ix_incident_service_status",
            "service_id",
            "status",
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
    trigger_anomaly_id: Mapped[UUID] = mapped_column(
        ForeignKey("anomaly_records.id", ondelete="CASCADE"),
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="open",
    )
    severity: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    acknowledged_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    resolved_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    resolution_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    service: Mapped[MonitoredService] = relationship(
        back_populates="incidents",
    )
    trigger_anomaly: Mapped[AnomalyRecord] = relationship(
        back_populates="incident",
    )
