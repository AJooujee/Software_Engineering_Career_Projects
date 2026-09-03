"""Database access operations for operational incidents."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.incident import Incident
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


def list_incidents(
    database_session: Session,
    *,
    offset: int = 0,
    limit: int = 100,
) -> list[Incident]:
    """Return incidents ordered from newest to oldest."""

    statement = (
        select(Incident)
        .order_by(Incident.created_at.desc())
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
