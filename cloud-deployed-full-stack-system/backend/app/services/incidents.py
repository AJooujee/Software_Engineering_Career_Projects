"""Business logic and transaction management for incidents."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit_event import AuditAction, AuditResourceType
from app.models.incident import (
    Incident,
    IncidentSeverity,
    IncidentStatus,
)
from app.models.user import User
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
import app.services.audit_events as audit_service


class IncidentNotFoundError(LookupError):
    """Raised when an incident cannot be found by its identifier."""

    def __init__(self, incident_id: UUID) -> None:
        """Store the missing identifier and create a readable message."""

        self.incident_id = incident_id
        super().__init__(f"Incident '{incident_id}' was not found.")


def create_incident(
    database_session: Session,
    incident_data: IncidentCreate,
    *,
    actor: User,
) -> Incident:
    """Create an Incident and its audit event in one transaction."""

    try:
        incident = create_incident_record(
            database_session,
            incident_data,
        )

        created_values = {
            "title": incident.title,
            "description": incident.description,
            "service_name": incident.service_name,
            "severity": incident.severity,
            "status": incident.status,
        }
        changes = audit_service.build_change_set(
            {
                field_name: None
                for field_name in created_values
            },
            created_values,
        )

        # Stage the audit entry before committing so either both records
        # succeed or the entire operation is rolled back.
        audit_service.record_audit_event(
            database_session,
            actor=actor,
            action=AuditAction.INCIDENT_CREATED,
            resource_type=AuditResourceType.INCIDENT,
            resource_id=incident.id,
            resource_label=incident.title,
            changes=changes,
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
    search: str | None = None,
    status: IncidentStatus | None = None,
    severity: IncidentSeverity | None = None,
    service_name: str | None = None,
    offset: int = 0,
    limit: int = 100,
) -> list[Incident]:
    """Return a filtered, paginated collection of Incidents."""

    return list_incident_records(
        database_session,
        search=search,
        status=status,
        severity=severity,
        service_name=service_name,
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
    *,
    actor: User,
) -> Incident:
    """Update an Incident and atomically record material changes."""

    incident = get_incident(database_session, incident_id)
    requested_values = incident_data.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )
    previous_values = {
        field_name: getattr(incident, field_name)
        for field_name in requested_values
    }
    changes = audit_service.build_change_set(
        previous_values,
        requested_values,
    )

    # A successful no-op does not change timestamps or create noise in
    # immutable audit history.
    if not changes:
        return incident

    try:
        updated_incident = update_incident_record(
            database_session,
            incident,
            incident_data,
        )

        audit_service.record_audit_event(
            database_session,
            actor=actor,
            action=AuditAction.INCIDENT_UPDATED,
            resource_type=AuditResourceType.INCIDENT,
            resource_id=updated_incident.id,
            resource_label=updated_incident.title,
            changes=changes,
        )

        database_session.commit()
        return updated_incident
    except Exception:
        # Roll back both the resource mutation and its audit event.
        database_session.rollback()
        raise


def delete_incident(
    database_session: Session,
    incident_id: UUID,
    *,
    actor: User,
) -> None:
    """Delete an Incident while retaining immutable audit history."""

    incident = get_incident(database_session, incident_id)
    resource_id = incident.id
    resource_label = incident.title

    try:
        delete_incident_record(
            database_session,
            incident,
        )

        # The audit resource identifier intentionally has no Incident
        # foreign key, allowing this event to survive the deletion.
        audit_service.record_audit_event(
            database_session,
            actor=actor,
            action=AuditAction.INCIDENT_DELETED,
            resource_type=AuditResourceType.INCIDENT,
            resource_id=resource_id,
            resource_label=resource_label,
            changes={
                "deleted": {
                    "from": False,
                    "to": True,
                }
            },
        )

        database_session.commit()
    except Exception:
        # Keep the resource and audit history consistent after failure.
        database_session.rollback()
        raise
