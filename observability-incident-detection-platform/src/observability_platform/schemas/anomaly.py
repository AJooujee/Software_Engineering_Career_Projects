from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from observability_platform.schemas.service import ServiceEnvironment


class AnomalyCategory(StrEnum):
    METRIC_THRESHOLD = "metric_threshold"
    LOG_SEVERITY = "log_severity"
    EVENT_SEVERITY = "event_severity"


class AnomalySeverity(StrEnum):
    WARNING = "warning"
    CRITICAL = "critical"


class AnomalyFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_id: str
    category: AnomalyCategory
    severity: AnomalySeverity
    title: str
    description: str
    service: str
    environment: ServiceEnvironment
    source: str
    observed_at: datetime
    observed_value: str | float
    threshold: str | float | None = None


class AnomalyRecordResponse(BaseModel):
    id: UUID
    telemetry_id: UUID
    rule_id: str
    category: AnomalyCategory
    severity: AnomalySeverity
    title: str
    description: str
    service: str
    environment: ServiceEnvironment
    source: str
    telemetry_type: Literal["metric", "log", "event"]
    observed_at: datetime
    detected_at: datetime
    observed_value: str | float
    threshold: str | float | None


class AnomalyQueryResponse(BaseModel):
    items: list[AnomalyRecordResponse]
    total: int
    limit: int
    offset: int
