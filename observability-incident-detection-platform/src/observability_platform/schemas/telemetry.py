from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from observability_platform.schemas.service import ServiceEnvironment


class LogLevel(StrEnum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class EventSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class TelemetryBase(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        allow_inf_nan=False,
    )

    service: str = Field(min_length=1, max_length=100)
    environment: ServiceEnvironment = ServiceEnvironment.DEVELOPMENT
    source: str = Field(min_length=1, max_length=200)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    attributes: dict[str, str | int | float | bool] = Field(default_factory=dict)


class MetricTelemetry(TelemetryBase):
    type: Literal["metric"] = "metric"
    name: str = Field(min_length=1, max_length=100)
    value: float
    unit: str | None = Field(default=None, max_length=30)


class LogTelemetry(TelemetryBase):
    type: Literal["log"] = "log"
    level: LogLevel
    message: str = Field(min_length=1, max_length=5000)


class EventTelemetry(TelemetryBase):
    type: Literal["event"] = "event"
    name: str = Field(min_length=1, max_length=100)
    severity: EventSeverity
    description: str | None = Field(default=None, max_length=2000)


TelemetryItem = Annotated[
    MetricTelemetry | LogTelemetry | EventTelemetry,
    Field(discriminator="type"),
]


class TelemetryBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[TelemetryItem] = Field(min_length=1, max_length=1000)


class TelemetryIngestResponse(BaseModel):
    accepted_count: int = Field(ge=0)
    telemetry_ids: list[UUID]
    received_at: datetime
    detected_anomaly_count: int = Field(default=0, ge=0)
    anomaly_ids: list[UUID] = Field(default_factory=list)
    created_incident_count: int = Field(default=0, ge=0)
    incident_ids: list[UUID] = Field(default_factory=list)


class TelemetryRecordResponse(BaseModel):
    id: UUID
    service_id: UUID
    service: str
    environment: ServiceEnvironment
    type: Literal["metric", "log", "event"]
    source: str
    observed_at: datetime
    received_at: datetime
    payload: dict[str, Any]


class TelemetryQueryResponse(BaseModel):
    items: list[TelemetryRecordResponse]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)
