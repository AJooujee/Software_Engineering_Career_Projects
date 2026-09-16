"""Pydantic request and response contracts for distributed tracing."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from observability_platform.schemas.service import ServiceEnvironment


class SpanStatus(StrEnum):
    """Describe the final execution state reported by a trace span."""

    # The instrumented operation did not explicitly report a result.
    UNSET = "unset"

    # The instrumented operation completed successfully.
    OK = "ok"

    # The instrumented operation completed with an error.
    ERROR = "error"


class TraceSpanCreate(BaseModel):
    """Validate one span submitted through the trace ingestion API."""

    # Reject undeclared fields and normalize surrounding string whitespace.
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    # W3C trace identifiers contain exactly 32 lowercase hexadecimal
    # characters and are shared by every span in one distributed trace.
    trace_id: str = Field(
        min_length=32,
        max_length=32,
        pattern=r"^[0-9a-f]{32}$",
    )

    # A span identifier contains exactly 16 lowercase hexadecimal characters
    # and identifies one operation inside a trace.
    span_id: str = Field(
        min_length=16,
        max_length=16,
        pattern=r"^[0-9a-f]{16}$",
    )

    # A root span has no parent. Child spans reference another span ID from
    # the same trace, which may arrive in the same or a later batch.
    parent_span_id: str | None = Field(
        default=None,
        min_length=16,
        max_length=16,
        pattern=r"^[0-9a-f]{16}$",
    )

    # Identify the registered service and runtime instance that emitted the
    # span so cross-service requests can be reconstructed.
    service: str = Field(min_length=1, max_length=100)
    environment: ServiceEnvironment
    source: str = Field(min_length=1, max_length=200)

    # Describe the operation represented by this span, such as an HTTP route,
    # database query, queue operation, or internal function.
    operation: str = Field(min_length=1, max_length=200)
    status: SpanStatus = SpanStatus.UNSET

    # Store an absolute time interval so the platform can calculate both
    # individual span latency and complete trace wall-clock duration.
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    ended_at: datetime

    # Attributes preserve protocol- or application-specific context without
    # requiring schema changes for every instrumentation library.
    attributes: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_timing_and_identity(self) -> "TraceSpanCreate":
        """Validate relationships that depend on more than one field."""

        # Negative durations indicate invalid instrumentation timestamps.
        if self.ended_at < self.started_at:
            raise ValueError("ended_at must be greater than or equal to started_at")

        # A span cannot be its own parent because that would introduce an
        # immediate cycle into the distributed trace graph.
        if self.parent_span_id == self.span_id:
            raise ValueError("parent_span_id must differ from span_id")

        # Return the validated model as required by an after-model validator.
        return self


class TraceBatchCreate(BaseModel):
    """Validate an atomic batch of spans submitted for one trace."""

    # Only the declared spans collection is accepted at the batch level.
    model_config = ConfigDict(extra="forbid")

    # Limit batch size to protect the API and database from unbounded requests.
    spans: list[TraceSpanCreate] = Field(
        min_length=1,
        max_length=1000,
    )


class TraceIngestResponse(BaseModel):
    """Report the result of a successful atomic trace ingestion."""

    # The count and IDs allow callers to reconcile accepted spans with their
    # persistent database records.
    accepted_count: int = Field(ge=0)
    span_record_ids: list[UUID]

    # One shared receive time represents when the platform accepted the batch.
    received_at: datetime


class TraceSpanResponse(BaseModel):
    """Represent one persistent span returned by the trace query API."""

    # Database identity is separate from the externally supplied W3C IDs.
    id: UUID
    trace_id: str
    span_id: str
    parent_span_id: str | None

    # Include resolved service identity to avoid requiring additional client
    # requests when displaying a multi-service trace.
    service_id: UUID
    service: str
    environment: ServiceEnvironment
    source: str

    # Operation and status describe the work represented by this span.
    operation: str
    status: SpanStatus

    # Return both timestamps and the precomputed duration used by dashboards.
    started_at: datetime
    ended_at: datetime
    duration_ms: float = Field(ge=0.0)

    # Preserve the original instrumentation context for debugging.
    attributes: dict[str, Any]


class TraceResponse(BaseModel):
    """Represent a complete distributed trace reconstructed from its spans."""

    trace_id: str

    # A stored trace must contain at least one span.
    span_count: int = Field(ge=1)

    # The trace interval covers the earliest start through the latest end,
    # including any overlapping span execution.
    started_at: datetime
    ended_at: datetime
    duration_ms: float = Field(ge=0.0)

    # List participating services once and return chronologically ordered spans.
    services: list[str]
    spans: list[TraceSpanResponse]
