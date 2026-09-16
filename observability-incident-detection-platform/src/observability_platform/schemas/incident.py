from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from observability_platform.schemas.service import ServiceEnvironment


class IncidentStatus(StrEnum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class IncidentSeverity(StrEnum):
    WARNING = "warning"
    CRITICAL = "critical"


class IncidentAcknowledgeRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    acknowledged_by: str = Field(min_length=1, max_length=100)


class IncidentResolveRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    resolved_by: str = Field(min_length=1, max_length=100)
    resolution_summary: str = Field(min_length=1, max_length=2000)


class IncidentResponse(BaseModel):
    id: UUID
    service_id: UUID
    trigger_anomaly_id: UUID
    service: str
    environment: ServiceEnvironment
    status: IncidentStatus
    severity: IncidentSeverity
    title: str
    description: str
    created_at: datetime
    acknowledged_at: datetime | None
    acknowledged_by: str | None
    resolved_at: datetime | None
    resolved_by: str | None
    resolution_summary: str | None


class IncidentQueryResponse(BaseModel):
    items: list[IncidentResponse]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)
