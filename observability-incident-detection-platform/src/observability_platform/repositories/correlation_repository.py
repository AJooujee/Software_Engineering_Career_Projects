from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from observability_platform.db.models import (
    AnomalyRecord,
    CorrelationIncidentRecord,
    CorrelationRecord,
    IncidentRecord,
    MonitoredService,
    TelemetryRecord,
)
from observability_platform.schemas.correlation import (
    CorrelationStatus,
    RootCauseCandidate,
)

CorrelationIncidentRow = tuple[
    IncidentRecord,
    AnomalyRecord,
    TelemetryRecord,
    MonitoredService,
]

CorrelationDetailRow = tuple[
    CorrelationRecord,
    MonitoredService,
    AnomalyRecord,
    IncidentRecord,
    TelemetryRecord,
]


class CorrelationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_uncorrelated_incidents(
        self,
        *,
        service: str,
        environment: str,
        window_started_at: datetime,
        window_ended_at: datetime,
    ) -> list[CorrelationIncidentRow]:
        statement = (
            select(
                IncidentRecord,
                AnomalyRecord,
                TelemetryRecord,
                MonitoredService,
            )
            .select_from(IncidentRecord)
            .join(
                AnomalyRecord,
                AnomalyRecord.id == IncidentRecord.trigger_anomaly_id,
            )
            .join(
                TelemetryRecord,
                TelemetryRecord.id == AnomalyRecord.telemetry_id,
            )
            .join(
                MonitoredService,
                MonitoredService.id == IncidentRecord.service_id,
            )
            .outerjoin(
                CorrelationIncidentRecord,
                CorrelationIncidentRecord.incident_id == IncidentRecord.id,
            )
            .where(
                MonitoredService.name == service,
                MonitoredService.environment == environment,
                IncidentRecord.created_at >= window_started_at,
                IncidentRecord.created_at <= window_ended_at,
                IncidentRecord.status != "resolved",
                CorrelationIncidentRecord.incident_id.is_(None),
            )
            .order_by(
                IncidentRecord.created_at,
                IncidentRecord.id,
            )
        )
        result = await self._session.execute(statement)

        return [
            (incident, anomaly, telemetry, monitored_service)
            for incident, anomaly, telemetry, monitored_service in result.all()
        ]

    async def create(
        self,
        *,
        service_id: UUID,
        incident_ids: list[UUID],
        root_cause: RootCauseCandidate,
        window_started_at: datetime,
        window_ended_at: datetime,
        summary: str,
        created_at: datetime,
    ) -> CorrelationRecord:
        correlation = CorrelationRecord(
            id=uuid4(),
            service_id=service_id,
            status=CorrelationStatus.ACTIVE.value,
            window_started_at=window_started_at,
            window_ended_at=window_ended_at,
            root_cause_anomaly_id=root_cause.anomaly_id,
            root_cause_incident_id=root_cause.incident_id,
            root_cause_confidence=root_cause.confidence_score,
            root_cause_reasons=root_cause.reasons,
            summary=summary,
            created_at=created_at,
            updated_at=created_at,
        )
        self._session.add(correlation)

        # Persist the parent before inserting junction rows that reference it.
        await self._session.flush()

        links = [
            CorrelationIncidentRecord(
                correlation_id=correlation.id,
                incident_id=incident_id,
                added_at=created_at,
            )
            for incident_id in incident_ids
        ]
        self._session.add_all(links)

        await self._session.flush()
        await self._session.refresh(correlation)

        return correlation

    async def get_by_id(
        self,
        correlation_id: UUID,
    ) -> CorrelationDetailRow | None:
        statement = (
            select(
                CorrelationRecord,
                MonitoredService,
                AnomalyRecord,
                IncidentRecord,
                TelemetryRecord,
            )
            .select_from(CorrelationRecord)
            .join(
                MonitoredService,
                MonitoredService.id == CorrelationRecord.service_id,
            )
            .join(
                AnomalyRecord,
                AnomalyRecord.id == CorrelationRecord.root_cause_anomaly_id,
            )
            .join(
                IncidentRecord,
                IncidentRecord.id == CorrelationRecord.root_cause_incident_id,
            )
            .join(
                TelemetryRecord,
                TelemetryRecord.id == AnomalyRecord.telemetry_id,
            )
            .where(CorrelationRecord.id == correlation_id)
        )
        result = await self._session.execute(statement)
        row = result.one_or_none()

        if row is None:
            return None

        correlation, service, anomaly, incident, telemetry = row
        return correlation, service, anomaly, incident, telemetry

    async def get_incident_ids(
        self,
        correlation_id: UUID,
    ) -> list[UUID]:
        statement = (
            select(CorrelationIncidentRecord.incident_id)
            .where(CorrelationIncidentRecord.correlation_id == correlation_id)
            .order_by(
                CorrelationIncidentRecord.added_at,
                CorrelationIncidentRecord.incident_id,
            )
        )
        result = await self._session.execute(statement)

        return list(result.scalars().all())

    async def query(
        self,
        *,
        service: str | None = None,
        environment: str | None = None,
        status: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[CorrelationDetailRow], int]:
        filters = []

        if service is not None:
            filters.append(MonitoredService.name == service)
        if environment is not None:
            filters.append(MonitoredService.environment == environment)
        if status is not None:
            filters.append(CorrelationRecord.status == status)
        if created_from is not None:
            filters.append(CorrelationRecord.created_at >= created_from)
        if created_to is not None:
            filters.append(CorrelationRecord.created_at <= created_to)

        count_statement = (
            select(func.count())
            .select_from(CorrelationRecord)
            .join(
                MonitoredService,
                MonitoredService.id == CorrelationRecord.service_id,
            )
            .where(*filters)
        )
        total = (await self._session.execute(count_statement)).scalar_one()

        query_statement = (
            select(
                CorrelationRecord,
                MonitoredService,
                AnomalyRecord,
                IncidentRecord,
                TelemetryRecord,
            )
            .select_from(CorrelationRecord)
            .join(
                MonitoredService,
                MonitoredService.id == CorrelationRecord.service_id,
            )
            .join(
                AnomalyRecord,
                AnomalyRecord.id == CorrelationRecord.root_cause_anomaly_id,
            )
            .join(
                IncidentRecord,
                IncidentRecord.id == CorrelationRecord.root_cause_incident_id,
            )
            .join(
                TelemetryRecord,
                TelemetryRecord.id == AnomalyRecord.telemetry_id,
            )
            .where(*filters)
            .order_by(
                CorrelationRecord.created_at.desc(),
                CorrelationRecord.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(query_statement)
        rows = [
            (correlation, monitored_service, anomaly, incident, telemetry)
            for (
                correlation,
                monitored_service,
                anomaly,
                incident,
                telemetry,
            ) in result.all()
        ]

        return rows, total
