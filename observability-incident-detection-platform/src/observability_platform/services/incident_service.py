from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from observability_platform.db.models import IncidentRecord, MonitoredService
from observability_platform.repositories.incident_repository import (
    IncidentRepository,
)
from observability_platform.schemas.incident import (
    IncidentQueryResponse,
    IncidentResponse,
    IncidentSeverity,
    IncidentStatus,
)
from observability_platform.schemas.service import ServiceEnvironment


class IncidentNotFoundError(Exception):
    pass


class InvalidIncidentTimeRangeError(ValueError):
    pass


class InvalidIncidentTransitionError(Exception):
    pass


class IncidentService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repository = IncidentRepository(session)

    async def get(self, incident_id: UUID) -> IncidentResponse:
        result = await self._repository.get_by_id(incident_id)

        if result is None:
            raise IncidentNotFoundError(f"Incident '{incident_id}' was not found")

        incident, service = result
        return self._to_response(incident, service)

    async def query(
        self,
        *,
        service: str | None = None,
        environment: ServiceEnvironment | None = None,
        status: IncidentStatus | None = None,
        severity: IncidentSeverity | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> IncidentQueryResponse:
        if (
            created_from is not None
            and created_to is not None
            and created_from > created_to
        ):
            raise InvalidIncidentTimeRangeError(
                "created_from must be earlier than or equal to created_to"
            )

        rows, total = await self._repository.query(
            service=service,
            environment=environment.value if environment is not None else None,
            status=status.value if status is not None else None,
            severity=severity.value if severity is not None else None,
            created_from=created_from,
            created_to=created_to,
            limit=limit,
            offset=offset,
        )

        return IncidentQueryResponse(
            items=[
                self._to_response(incident, monitored_service)
                for incident, monitored_service in rows
            ],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def acknowledge(
        self,
        incident_id: UUID,
        *,
        acknowledged_by: str,
    ) -> IncidentResponse:
        incident, service = await self._get_record(incident_id)

        if incident.status != IncidentStatus.OPEN.value:
            raise InvalidIncidentTransitionError(
                f"Incident in status '{incident.status}' cannot be acknowledged"
            )

        incident.status = IncidentStatus.ACKNOWLEDGED.value
        incident.acknowledged_at = datetime.now(UTC)
        incident.acknowledged_by = acknowledged_by

        try:
            await self._repository.save(incident)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

        return self._to_response(incident, service)

    async def resolve(
        self,
        incident_id: UUID,
        *,
        resolved_by: str,
        resolution_summary: str,
    ) -> IncidentResponse:
        incident, service = await self._get_record(incident_id)

        if incident.status == IncidentStatus.RESOLVED.value:
            raise InvalidIncidentTransitionError(
                "Resolved incident cannot be resolved again"
            )

        incident.status = IncidentStatus.RESOLVED.value
        incident.resolved_at = datetime.now(UTC)
        incident.resolved_by = resolved_by
        incident.resolution_summary = resolution_summary

        try:
            await self._repository.save(incident)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

        return self._to_response(incident, service)

    async def _get_record(
        self,
        incident_id: UUID,
    ) -> tuple[IncidentRecord, MonitoredService]:
        result = await self._repository.get_by_id(incident_id)

        if result is None:
            raise IncidentNotFoundError(f"Incident '{incident_id}' was not found")

        return result

    @staticmethod
    def _to_response(
        incident: IncidentRecord,
        service: MonitoredService,
    ) -> IncidentResponse:
        return IncidentResponse(
            id=incident.id,
            service_id=incident.service_id,
            trigger_anomaly_id=incident.trigger_anomaly_id,
            service=service.name,
            environment=service.environment,
            status=incident.status,
            severity=incident.severity,
            title=incident.title,
            description=incident.description,
            created_at=incident.created_at,
            acknowledged_at=incident.acknowledged_at,
            acknowledged_by=incident.acknowledged_by,
            resolved_at=incident.resolved_at,
            resolved_by=incident.resolved_by,
            resolution_summary=incident.resolution_summary,
        )
