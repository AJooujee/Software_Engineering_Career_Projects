"""Database aggregation queries for operational dashboard metrics."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.incident import (
    Incident,
    IncidentSeverity,
    IncidentStatus,
)


def count_incidents_by_status(
    database_session: Session,
) -> dict[IncidentStatus, int]:
    """Return every lifecycle status with its current Incident count."""

    # Initialize every enum value so empty categories remain visible
    # in the stable API response.
    counts = {
        incident_status: 0
        for incident_status in IncidentStatus
    }

    statement = (
        select(
            Incident.status,
            func.count(Incident.id),
        )
        .group_by(Incident.status)
    )

    for incident_status, count in database_session.execute(
        statement
    ):
        counts[incident_status] = int(count)

    return counts


def count_incidents_by_severity(
    database_session: Session,
) -> dict[IncidentSeverity, int]:
    """Return every severity with its current Incident count."""

    counts = {
        incident_severity: 0
        for incident_severity in IncidentSeverity
    }

    statement = (
        select(
            Incident.severity,
            func.count(Incident.id),
        )
        .group_by(Incident.severity)
    )

    for incident_severity, count in database_session.execute(
        statement
    ):
        counts[incident_severity] = int(count)

    return counts


def count_affected_services(
    database_session: Session,
) -> int:
    """Count distinct services with an active operational Incident."""

    active_statuses = (
        IncidentStatus.OPEN,
        IncidentStatus.INVESTIGATING,
    )

    statement = (
        select(
            func.count(
                func.distinct(Incident.service_name)
            )
        )
        .where(Incident.status.in_(active_statuses))
    )

    return int(database_session.scalar(statement) or 0)
