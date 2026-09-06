"""Database access operations for operational incidents."""

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.incident import (
    Incident,
    IncidentSeverity,
    IncidentStatus,
)
from app.schemas.incident import IncidentCreate, IncidentUpdate


def create_incident(
    database_session: Session,
    incident_data: IncidentCreate,
) -> Incident:
    """Stage a new incident in the current database transaction."""

    incident = Incident(**incident_data.model_dump())

    database_session.add(incident)
    database_session.flush()
    database_session.refresh(incident)

    return incident


def escape_like_value(value: str) -> str:
    """Escape SQL wildcard characters so search terms remain literal."""

    return (
        value.replace("\\", "\\\\")
        .replace("%", r"\%")
        .replace("_", r"\_")
    )


def list_incidents(
    database_session: Session,
    *,
    search: str | None = None,
    status: IncidentStatus | None = None,
    severity: IncidentSeverity | None = None,
    service_name: str | None = None,
    offset: int = 0,
    limit: int = 100,
) -> list[Incident]:
    """Return filtered incidents ordered from newest to oldest."""

    statement = select(Incident)

    # Search the human-readable Incident fields without treating user input
    # as SQL wildcard syntax.
    normalized_search = search.strip() if search else ""

    if normalized_search:
        escaped_search = escape_like_value(normalized_search)
        search_pattern = f"%{escaped_search}%"

        statement = statement.where(
            or_(
                Incident.title.ilike(
                    search_pattern,
                    escape="\\",
                ),
                Incident.description.ilike(
                    search_pattern,
                    escape="\\",
                ),
                Incident.service_name.ilike(
                    search_pattern,
                    escape="\\",
                ),
            )
        )

    # Service filtering uses a normalized exact match so similarly named
    # services do not appear in the same result set.
    normalized_service_name = (
        service_name.strip().lower()
        if service_name
        else ""
    )

    if normalized_service_name:
        statement = statement.where(
            func.lower(Incident.service_name)
            == normalized_service_name
        )

    if status is not None:
        statement = statement.where(
            Incident.status == status,
        )

    if severity is not None:
        statement = statement.where(
            Incident.severity == severity,
        )

    statement = (
        statement
        .order_by(
            Incident.created_at.desc(),
            Incident.id.desc(),
        )
        .offset(offset)
        .limit(limit)
    )

    return list(database_session.scalars(statement).all())


def get_incident(
    database_session: Session,
    incident_id: UUID,
) -> Incident | None:
    """Return one incident by primary key or None when it does not exist."""

    return database_session.get(Incident, incident_id)


def update_incident(
    database_session: Session,
    incident: Incident,
    incident_data: IncidentUpdate,
) -> Incident:
    """Apply provided fields to an existing incident."""

    # Ignore omitted and explicit null fields to protect required columns.
    changes = incident_data.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    for field_name, value in changes.items():
        setattr(incident, field_name, value)

    database_session.add(incident)
    database_session.flush()
    database_session.refresh(incident)

    return incident


def delete_incident(
    database_session: Session,
    incident: Incident,
) -> None:
    """Stage an existing incident for deletion."""

    database_session.delete(incident)
    database_session.flush()
