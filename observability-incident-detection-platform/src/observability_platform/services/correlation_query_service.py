from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from observability_platform.repositories.correlation_repository import (
    CorrelationDetailRow,
    CorrelationRepository,
)
from observability_platform.schemas.anomaly import (
    AnomalyCategory,
    AnomalySeverity,
)
from observability_platform.schemas.correlation import (
    CorrelationQueryResponse,
    CorrelationResponse,
    RootCauseCandidate,
)


class CorrelationNotFoundError(Exception):
    pass


class CorrelationQueryService:
    def __init__(self, session: AsyncSession) -> None:
        self._repository = CorrelationRepository(session)

    async def get_by_id(
        self,
        correlation_id: UUID,
    ) -> CorrelationResponse:
        row = await self._repository.get_by_id(correlation_id)

        if row is None:
            raise CorrelationNotFoundError(
                f"Correlation '{correlation_id}' was not found"
            )

        return await self._to_response(row)

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
    ) -> CorrelationQueryResponse:
        rows, total = await self._repository.query(
            service=service,
            environment=environment,
            status=status,
            created_from=created_from,
            created_to=created_to,
            limit=limit,
            offset=offset,
        )
        items = [await self._to_response(row) for row in rows]

        return CorrelationQueryResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )

    async def _to_response(
        self,
        row: CorrelationDetailRow,
    ) -> CorrelationResponse:
        correlation, service, anomaly, incident, telemetry = row
        incident_ids = await self._repository.get_incident_ids(correlation.id)

        root_cause = RootCauseCandidate(
            anomaly_id=anomaly.id,
            incident_id=incident.id,
            rule_id=anomaly.rule_id,
            category=AnomalyCategory(anomaly.category),
            severity=AnomalySeverity(anomaly.severity),
            source=telemetry.source,
            observed_at=telemetry.observed_at,
            confidence_score=correlation.root_cause_confidence,
            reasons=correlation.root_cause_reasons,
        )

        return CorrelationResponse(
            id=correlation.id,
            service_id=service.id,
            service=service.name,
            environment=service.environment,
            status=correlation.status,
            incident_ids=incident_ids,
            incident_count=len(incident_ids),
            window_started_at=correlation.window_started_at,
            window_ended_at=correlation.window_ended_at,
            root_cause=root_cause,
            summary=correlation.summary,
            created_at=correlation.created_at,
            updated_at=correlation.updated_at,
        )
