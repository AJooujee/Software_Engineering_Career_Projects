from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from observability_platform.db.models import TelemetryRecord
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
