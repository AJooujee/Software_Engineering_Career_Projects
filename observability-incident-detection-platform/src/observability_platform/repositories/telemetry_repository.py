from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from observability_platform.db.models import MonitoredService, TelemetryRecord
from observability_platform.schemas.telemetry import TelemetryItem


class TelemetryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_batch(
        self,
        items: list[tuple[TelemetryItem, UUID]],
        *,
        received_at: datetime,
    ) -> list[TelemetryRecord]:
        records = [
            TelemetryRecord(
                id=uuid4(),
                service_id=service_id,
                telemetry_type=item.type,
                source=item.source,
                observed_at=item.timestamp,
                received_at=received_at,
                payload=item.model_dump(mode="json"),
            )
            for item, service_id in items
        ]

        self._session.add_all(records)
        await self._session.flush()

        return records

    async def query(
        self,
        *,
        service: str | None = None,
        environment: str | None = None,
        telemetry_type: str | None = None,
        source: str | None = None,
        observed_from: datetime | None = None,
        observed_to: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[tuple[TelemetryRecord, MonitoredService]], int]:
        filters = []

        if service is not None:
            filters.append(MonitoredService.name == service)
        if environment is not None:
            filters.append(MonitoredService.environment == environment)
        if telemetry_type is not None:
            filters.append(TelemetryRecord.telemetry_type == telemetry_type)
        if source is not None:
            filters.append(TelemetryRecord.source == source)
        if observed_from is not None:
            filters.append(TelemetryRecord.observed_at >= observed_from)
        if observed_to is not None:
            filters.append(TelemetryRecord.observed_at <= observed_to)

        count_statement = (
            select(func.count())
            .select_from(TelemetryRecord)
            .join(MonitoredService)
            .where(*filters)
        )
        total = (await self._session.execute(count_statement)).scalar_one()

        query_statement = (
            select(TelemetryRecord, MonitoredService)
            .join(MonitoredService)
            .where(*filters)
            .order_by(
                TelemetryRecord.observed_at.desc(),
                TelemetryRecord.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(query_statement)
        rows = [
            (record, monitored_service) for record, monitored_service in result.all()
        ]

        return rows, total
