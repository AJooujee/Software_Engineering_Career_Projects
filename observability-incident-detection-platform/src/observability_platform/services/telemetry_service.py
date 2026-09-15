from asyncio import Lock
from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from observability_platform.schemas.telemetry import (
    TelemetryBatch,
    TelemetryIngestResponse,
    TelemetryItem,
)


@dataclass(frozen=True, slots=True)
class StoredTelemetry:
    telemetry_id: UUID
    data: TelemetryItem
    received_at: datetime


class InMemoryTelemetryStore:
    def __init__(self, max_items: int = 10_000) -> None:
        if max_items < 1:
            raise ValueError("max_items must be greater than zero")

        self._items: deque[StoredTelemetry] = deque(maxlen=max_items)
        self._lock = Lock()

    async def ingest(self, batch: TelemetryBatch) -> TelemetryIngestResponse:
        received_at = datetime.now(UTC)
        records = [
            StoredTelemetry(
                telemetry_id=uuid4(),
                data=item,
                received_at=received_at,
            )
            for item in batch.items
        ]

        async with self._lock:
            self._items.extend(records)

        return TelemetryIngestResponse(
            accepted_count=len(records),
            telemetry_ids=[record.telemetry_id for record in records],
            received_at=received_at,
        )

    async def count(self) -> int:
        async with self._lock:
            return len(self._items)

    async def list_items(self) -> list[StoredTelemetry]:
        async with self._lock:
            return list(self._items)

    async def clear(self) -> None:
        async with self._lock:
            self._items.clear()


telemetry_store = InMemoryTelemetryStore()
