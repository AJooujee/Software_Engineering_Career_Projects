from datetime import datetime
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from observability_platform.repositories.telemetry_repository import (
    TelemetryRepository,
)
from observability_platform.schemas.service import ServiceEnvironment
from observability_platform.schemas.telemetry import (
    TelemetryQueryResponse,
    TelemetryRecordResponse,
)


class InvalidTelemetryTimeRangeError(ValueError):
    pass


class TelemetryQueryService:
    def __init__(self, session: AsyncSession) -> None:
        self._repository = TelemetryRepository(session)

    async def query(
        self,
        *,
        service: str | None = None,
        environment: ServiceEnvironment | None = None,
        telemetry_type: Literal["metric", "log", "event"] | None = None,
        source: str | None = None,
        observed_from: datetime | None = None,
        observed_to: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> TelemetryQueryResponse:
        if (
            observed_from is not None
            and observed_to is not None
            and observed_from > observed_to
        ):
            raise InvalidTelemetryTimeRangeError(
                "observed_from must be earlier than or equal to observed_to"
            )

        rows, total = await self._repository.query(
            service=service,
            environment=environment.value if environment is not None else None,
            telemetry_type=telemetry_type,
            source=source,
            observed_from=observed_from,
            observed_to=observed_to,
            limit=limit,
            offset=offset,
        )

        items = [
            TelemetryRecordResponse(
                id=record.id,
                service_id=record.service_id,
                service=monitored_service.name,
                environment=monitored_service.environment,
                type=record.telemetry_type,
                source=record.source,
                observed_at=record.observed_at,
                received_at=record.received_at,
                payload=record.payload,
            )
            for record, monitored_service in rows
        ]

        return TelemetryQueryResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )
