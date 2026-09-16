from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from observability_platform.db.models import (
    AnomalyRecord,
    IncidentRecord,
    MonitoredService,
)
from observability_platform.schemas.incident import IncidentStatus


class IncidentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_batch(
        self,
        anomalies: list[tuple[AnomalyRecord, UUID]],
        *,
        created_at: datetime,
    ) -> list[IncidentRecord]:
        incidents = [
            IncidentRecord(
                id=uuid4(),
                service_id=service_id,
                trigger_anomaly_id=anomaly.id,
                status=IncidentStatus.OPEN.value,
                severity=anomaly.severity,
                title=f"Incident: {anomaly.title}",
                description=anomaly.description,
                created_at=created_at,
            )
            for anomaly, service_id in anomalies
        ]

        self._session.add_all(incidents)
        await self._session.flush()

        return incidents

    async def get_by_id(
        self,
        incident_id: UUID,
    ) -> tuple[IncidentRecord, MonitoredService] | None:
        statement = (
            select(IncidentRecord, MonitoredService)
            .select_from(IncidentRecord)
            .join(
                MonitoredService,
                MonitoredService.id == IncidentRecord.service_id,
            )
            .where(IncidentRecord.id == incident_id)
        )
        result = await self._session.execute(statement)
        row = result.one_or_none()

        if row is None:
            return None

        incident, service = row
        return incident, service

    async def query(
        self,
        *,
        service: str | None = None,
        environment: str | None = None,
        status: str | None = None,
        severity: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[tuple[IncidentRecord, MonitoredService]], int]:
        filters = []

        if service is not None:
            filters.append(MonitoredService.name == service)
        if environment is not None:
            filters.append(MonitoredService.environment == environment)
        if status is not None:
            filters.append(IncidentRecord.status == status)
        if severity is not None:
            filters.append(IncidentRecord.severity == severity)
        if created_from is not None:
            filters.append(IncidentRecord.created_at >= created_from)
        if created_to is not None:
            filters.append(IncidentRecord.created_at <= created_to)

        count_statement = (
            select(func.count())
            .select_from(IncidentRecord)
            .join(
                MonitoredService,
                MonitoredService.id == IncidentRecord.service_id,
            )
            .where(*filters)
        )
        total = (await self._session.execute(count_statement)).scalar_one()

        query_statement = (
            select(IncidentRecord, MonitoredService)
            .select_from(IncidentRecord)
            .join(
                MonitoredService,
                MonitoredService.id == IncidentRecord.service_id,
            )
            .where(*filters)
            .order_by(
                IncidentRecord.created_at.desc(),
                IncidentRecord.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(query_statement)
        rows = [
            (incident, monitored_service)
            for incident, monitored_service in result.all()
        ]

        return rows, total

    async def save(
        self,
        incident: IncidentRecord,
    ) -> IncidentRecord:
        await self._session.flush()
        await self._session.refresh(incident)

        return incident
