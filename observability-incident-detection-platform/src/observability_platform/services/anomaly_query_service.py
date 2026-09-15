from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from observability_platform.repositories.anomaly_repository import (
    AnomalyRepository,
)
from observability_platform.schemas.anomaly import (
    AnomalyCategory,
    AnomalyQueryResponse,
    AnomalyRecordResponse,
    AnomalySeverity,
)
from observability_platform.schemas.service import ServiceEnvironment


class InvalidAnomalyTimeRangeError(ValueError):
    pass


class AnomalyQueryService:
    def __init__(self, session: AsyncSession) -> None:
        self._repository = AnomalyRepository(session)

    async def query(
        self,
        *,
        service: str | None = None,
        environment: ServiceEnvironment | None = None,
        category: AnomalyCategory | None = None,
        severity: AnomalySeverity | None = None,
        rule_id: str | None = None,
        detected_from: datetime | None = None,
        detected_to: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> AnomalyQueryResponse:
        if (
            detected_from is not None
            and detected_to is not None
            and detected_from > detected_to
        ):
            raise InvalidAnomalyTimeRangeError(
                "detected_from must be earlier than or equal to detected_to"
            )

        rows, total = await self._repository.query(
            service=service,
            environment=environment.value if environment is not None else None,
            category=category.value if category is not None else None,
            severity=severity.value if severity is not None else None,
            rule_id=rule_id,
            detected_from=detected_from,
            detected_to=detected_to,
            limit=limit,
            offset=offset,
        )

        items = [
            AnomalyRecordResponse(
                id=anomaly.id,
                telemetry_id=anomaly.telemetry_id,
                rule_id=anomaly.rule_id,
                category=anomaly.category,
                severity=anomaly.severity,
                title=anomaly.title,
                description=anomaly.description,
                service=monitored_service.name,
                environment=monitored_service.environment,
                source=telemetry.source,
                telemetry_type=telemetry.telemetry_type,
                observed_at=telemetry.observed_at,
                detected_at=anomaly.detected_at,
                observed_value=anomaly.observed_value,
                threshold=anomaly.threshold,
            )
            for anomaly, telemetry, monitored_service in rows
        ]

        return AnomalyQueryResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )
