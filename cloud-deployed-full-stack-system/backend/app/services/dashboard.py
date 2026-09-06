"""Business logic for operational dashboard metrics."""

from sqlalchemy.orm import Session

from app.models.incident import IncidentSeverity, IncidentStatus
import app.repositories.dashboard as dashboard_repository
from app.schemas.dashboard import (
    DashboardSummary,
    IncidentSeverityCounts,
    IncidentStatusCounts,
)


def get_dashboard_summary(
    database_session: Session,
) -> DashboardSummary:
    """Build a stable dashboard summary from current Incident data."""

    status_counts = dashboard_repository.count_incidents_by_status(
        database_session,
    )
    severity_counts = (
        dashboard_repository.count_incidents_by_severity(
            database_session,
        )
    )

    # Active work includes newly opened and investigating Incidents.
    active_incidents = (
        status_counts[IncidentStatus.OPEN]
        + status_counts[IncidentStatus.INVESTIGATING]
    )

    return DashboardSummary(
        total_incidents=sum(status_counts.values()),
        active_incidents=active_incidents,
        critical_incidents=severity_counts[
            IncidentSeverity.CRITICAL
        ],
        resolved_incidents=status_counts[
            IncidentStatus.RESOLVED
        ],
        affected_services=(
            dashboard_repository.count_affected_services(
                database_session,
            )
        ),
        status_counts=IncidentStatusCounts(
            open=status_counts[IncidentStatus.OPEN],
            investigating=status_counts[
                IncidentStatus.INVESTIGATING
            ],
            resolved=status_counts[IncidentStatus.RESOLVED],
            closed=status_counts[IncidentStatus.CLOSED],
        ),
        severity_counts=IncidentSeverityCounts(
            low=severity_counts[IncidentSeverity.LOW],
            medium=severity_counts[IncidentSeverity.MEDIUM],
            high=severity_counts[IncidentSeverity.HIGH],
            critical=severity_counts[
                IncidentSeverity.CRITICAL
            ],
        ),
    )
