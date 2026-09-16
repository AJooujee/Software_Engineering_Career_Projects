from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from observability_platform.schemas.anomaly import (
    AnomalyCategory,
    AnomalySeverity,
)
from observability_platform.schemas.service import ServiceEnvironment


class CorrelationStatus(StrEnum):
    ACTIVE = "active"
    CLOSED = "closed"


class CorrelationAnalyzeRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    service: str = Field(min_length=1, max_length=100)
    environment: ServiceEnvironment
    window_minutes: int = Field(default=15, ge=1, le=1440)
    minimum_incidents: int = Field(default=2, ge=2, le=100)


class RootCauseCandidate(BaseModel):
    anomaly_id: UUID
    incident_id: UUID
    rule_id: str
    category: AnomalyCategory
    severity: AnomalySeverity
    source: str
    observed_at: datetime
    confidence_score: float = Field(ge=0.0, le=1.0)
    reasons: list[str]


class CorrelationResponse(BaseModel):
    id: UUID
    service_id: UUID
    service: str
    environment: ServiceEnvironment
    status: CorrelationStatus
    incident_ids: list[UUID]
    incident_count: int = Field(ge=2)
    window_started_at: datetime
    window_ended_at: datetime
    root_cause: RootCauseCandidate
    summary: str
    created_at: datetime
    updated_at: datetime


class CorrelationQueryResponse(BaseModel):
    items: list[CorrelationResponse]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)
