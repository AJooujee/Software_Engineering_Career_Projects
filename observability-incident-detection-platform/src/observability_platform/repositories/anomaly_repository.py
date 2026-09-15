from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from observability_platform.db.models import (
    AnomalyRecord,
    MonitoredService,
    TelemetryRecord,
)
from observability_platform.schemas.anomaly import AnomalyFinding


class AnomalyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_batch(
        self,
        findings: list[tuple[AnomalyFinding, UUID]],
        *,
        detected_at: datetime,
    ) -> list[AnomalyRecord]:
        records = [
            AnomalyRecord(
                id=uuid4(),
                telemetry_id=telemetry_id,
                rule_id=finding.rule_id,
                category=finding.category.value,
                severity=finding.severity.value,
                title=finding.title,
                description=finding.description,
                observed_value=finding.observed_value,
                threshold=finding.threshold,
                detected_at=detected_at,
            )
            for finding, telemetry_id in findings
        ]

        self._session.add_all(records)
        await self._session.flush()

        return records

    async def query(
        self,
        *,
        service: str | None = None,
        environment: str | None = None,
        category: str | None = None,
        severity: str | None = None,
        rule_id: str | None = None,
        detected_from: datetime | None = None,
        detected_to: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[
        list[tuple[AnomalyRecord, TelemetryRecord, MonitoredService]],
        int,
    ]:
        filters = []

        if service is not None:
            filters.append(MonitoredService.name == service)
        if environment is not None:
            filters.append(MonitoredService.environment == environment)
        if category is not None:
            filters.append(AnomalyRecord.category == category)
        if severity is not None:
            filters.append(AnomalyRecord.severity == severity)
        if rule_id is not None:
            filters.append(AnomalyRecord.rule_id == rule_id)
        if detected_from is not None:
            filters.append(AnomalyRecord.detected_at >= detected_from)
        if detected_to is not None:
            filters.append(AnomalyRecord.detected_at <= detected_to)

        count_statement = (
            select(func.count())
            .select_from(AnomalyRecord)
            .join(
                TelemetryRecord,
                TelemetryRecord.id == AnomalyRecord.telemetry_id,
            )
            .join(
                MonitoredService,
                MonitoredService.id == TelemetryRecord.service_id,
            )
            .where(*filters)
        )
        total = (await self._session.execute(count_statement)).scalar_one()

        query_statement = (
            select(
                AnomalyRecord,
                TelemetryRecord,
                MonitoredService,
            )
            .select_from(AnomalyRecord)
            .join(
                TelemetryRecord,
                TelemetryRecord.id == AnomalyRecord.telemetry_id,
            )
            .join(
                MonitoredService,
                MonitoredService.id == TelemetryRecord.service_id,
            )
            .where(*filters)
            .order_by(
                AnomalyRecord.detected_at.desc(),
                AnomalyRecord.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(query_statement)
        rows = [
            (anomaly, telemetry, monitored_service)
            for anomaly, telemetry, monitored_service in result.all()
        ]

        return rows, total
