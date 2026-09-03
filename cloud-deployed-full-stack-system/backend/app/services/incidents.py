"""Business logic and transaction management for incidents."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.repositories import (
    create_incident as create_incident_record,
)
from app.repositories import (
    delete_incident as delete_incident_record,
)
from app.repositories import (
    get_incident as get_incident_record,
)
from app.repositories import (
    list_incidents as list_incident_records,
)
from app.repositories import (
    update_incident as update_incident_record,
)
from app.schemas.incident import IncidentCreate, IncidentUpdate


class IncidentNotFoundError(LookupError):
    """Raised when an incident cannot be found by its identifier."""

    def __init__(self, incident_id: UUID) -> None:
        """Store the missing identifier and create a readable message."""

        self.incident_id = incident_id
        super().__init__(f"Incident '{incident_id}' was not found.")


def create_incident(
    database_session: Session,
    incident_data: IncidentCreate,
) -> Incident:
    """Create and commit a new operational incident."""

    try:
        incident = create_incident_record(
            database_session,
            incident_data,
        )
        database_session.commit()
        return incident
    except Exception:
        # Restore the session before propagating any database error.
        database_session.rollback()
        raise


def list_incidents(
    database_session: Session,
    *,
    offset: int = 0,
    limit: int = 100,
) -> list[Incident]:
    """Return a paginated collection of operational incidents."""

    return list_incident_records(
        database_session,
        offset=offset,
        limit=limit,
    )


def get_incident(
    database_session: Session,
    incident_id: UUID,
) -> Incident:
    """Return an incident or raise a domain-specific not-found error."""

    incident = get_incident_record(
        database_session,
        incident_id,
    )

    if incident is None:
        raise IncidentNotFoundError(incident_id)

    return incident


def update_incident(
    database_session: Session,
    incident_id: UUID,
    incident_data: IncidentUpdate,
) -> Incident:
    """Update and commit an existing operational incident."""

    incident = get_incident(database_session, incident_id)

    try:
        updated_incident = update_incident_record(
            database_session,
            incident,
            incident_data,
        )
        database_session.commit()
        return updated_incident
    except Exception:
        # Roll back partial changes if validation or persistence fails.
        database_session.rollback()
        raise


def delete_incident(
    database_session: Session,
    incident_id: UUID,
) -> None:
    """Delete and commit an existing operational incident."""

    incident = get_incident(database_session, incident_id)

    try:
        delete_incident_record(
            database_session,
            incident,
        )
        database_session.commit()
    except Exception:
        # Keep the shared session reusable after a failed deletion.
        database_session.rollback()
        raise
