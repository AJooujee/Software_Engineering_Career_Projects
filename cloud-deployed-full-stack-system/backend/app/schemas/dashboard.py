"""Pydantic response schemas for operational dashboard metrics."""

from pydantic import BaseModel, Field


class IncidentStatusCounts(BaseModel):
    """Expose a stable count for every Incident lifecycle status."""

    open: int = Field(ge=0)
    investigating: int = Field(ge=0)
    resolved: int = Field(ge=0)
    closed: int = Field(ge=0)


class IncidentSeverityCounts(BaseModel):
    """Expose a stable count for every Incident severity."""

    low: int = Field(ge=0)
    medium: int = Field(ge=0)
    high: int = Field(ge=0)
    critical: int = Field(ge=0)


class DashboardSummary(BaseModel):
    """Return the metrics required by the operational dashboard."""

    total_incidents: int = Field(ge=0)
    active_incidents: int = Field(ge=0)
    critical_incidents: int = Field(ge=0)
    resolved_incidents: int = Field(ge=0)
    affected_services: int = Field(ge=0)
    status_counts: IncidentStatusCounts
    severity_counts: IncidentSeverityCounts
