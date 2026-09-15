from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from observability_platform.repositories.anomaly_repository import (
    AnomalyRepository,
)
from observability_platform.repositories.service_repository import (
    ServiceRepository,
)
from observability_platform.repositories.telemetry_repository import (
    TelemetryRepository,
)
from observability_platform.schemas.service import ServiceEnvironment
from observability_platform.schemas.telemetry import (
    TelemetryBatch,
    TelemetryIngestResponse,
)
from observability_platform.services.anomaly_detection import (
    AnomalyDetectionEngine,
)


class UnregisteredServiceError(Exception):
    pass


class PersistentTelemetryService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._service_repository = ServiceRepository(session)
        self._telemetry_repository = TelemetryRepository(session)
        self._anomaly_repository = AnomalyRepository(session)
        self._detection_engine = AnomalyDetectionEngine()

    async def ingest(
        self,
        batch: TelemetryBatch,
    ) -> TelemetryIngestResponse:
        service_ids: dict[tuple[str, ServiceEnvironment], UUID] = {}
        resolved_items = []

        for item in batch.items:
            identity = (item.service, item.environment)
            service_id = service_ids.get(identity)

            if service_id is None:
                service = await self._service_repository.get_by_identity(
                    item.service,
                    item.environment,
                )
                if service is None:
                    raise UnregisteredServiceError(
                        f"Service '{item.service}' is not registered "
                        f"in environment '{item.environment.value}'"
                    )

                service_id = service.id
                service_ids[identity] = service_id

            resolved_items.append((item, service_id))

        received_at = datetime.now(UTC)

        try:
            records = await self._telemetry_repository.create_batch(
                resolved_items,
                received_at=received_at,
            )

            findings_with_telemetry_ids = [
                (finding, record.id)
                for item, record in zip(
                    batch.items,
                    records,
                    strict=True,
                )
                for finding in self._detection_engine.evaluate(item)
            ]
            anomaly_records = await self._anomaly_repository.create_batch(
                findings_with_telemetry_ids,
                detected_at=received_at,
            )

            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

        return TelemetryIngestResponse(
            accepted_count=len(records),
            telemetry_ids=[record.id for record in records],
            received_at=received_at,
            detected_anomaly_count=len(anomaly_records),
            anomaly_ids=[record.id for record in anomaly_records],
        )
