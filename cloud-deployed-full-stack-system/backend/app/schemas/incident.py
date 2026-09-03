"""Pydantic request and response schemas for incident operations."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.incident import IncidentSeverity, IncidentStatus


class IncidentBase(BaseModel):
    """Fields shared by incident creation and response schemas."""

    title: str = Field(
        min_length=3,
        max_length=200,
        examples=["Payment API latency"],
    )
    description: str = Field(
        min_length=1,
        max_length=5000,
        examples=["Response times exceeded the service-level objective."],
    )
    service_name: str = Field(
        min_length=2,
        max_length=120,
        examples=["payment-api"],
    )
    severity: IncidentSeverity = IncidentSeverity.MEDIUM

    # Remove unnecessary surrounding whitespace from user input.
    model_config = ConfigDict(str_strip_whitespace=True)


class IncidentCreate(IncidentBase):
    """Payload accepted when a new incident is created."""


class IncidentUpdate(BaseModel):
    """Optional fields accepted when an incident is updated."""

    title: str | None = Field(
        default=None,
        min_length=3,
        max_length=200,
    )
    description: str | None = Field(
        default=None,
        min_length=1,
        max_length=5000,
    )
    service_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=120,
    )
    severity: IncidentSeverity | None = None
    status: IncidentStatus | None = None

    model_config = ConfigDict(str_strip_whitespace=True)


class IncidentResponse(IncidentBase):
    """Incident data returned from the REST API."""

    id: UUID
    status: IncidentStatus
    created_at: datetime
    updated_at: datetime

    # Allow Pydantic to serialize SQLAlchemy model instances.
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
    )