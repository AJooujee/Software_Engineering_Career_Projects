from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from observability_platform.repositories.correlation_repository import (
    CorrelationRepository,
)
from observability_platform.schemas.anomaly import (
    AnomalyCategory,
    AnomalySeverity,
)
from observability_platform.schemas.correlation import (
    CorrelationAnalyzeRequest,
    CorrelationResponse,
)
from observability_platform.services.root_cause_analysis import (
    CorrelationSignal,
    RootCauseAnalysisEngine,
)


class InsufficientIncidentsError(Exception):
    pass


class CorrelationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repository = CorrelationRepository(session)
        self._analysis_engine = RootCauseAnalysisEngine()

    async def analyze(
        self,
        request: CorrelationAnalyzeRequest,
    ) -> CorrelationResponse:
        window_ended_at = datetime.now(UTC)
        window_started_at = window_ended_at - timedelta(minutes=request.window_minutes)

        rows = await self._repository.find_uncorrelated_incidents(
            service=request.service,
            environment=request.environment.value,
            window_started_at=window_started_at,
            window_ended_at=window_ended_at,
        )

        if len(rows) < request.minimum_incidents:
            raise InsufficientIncidentsError(
                f"Found {len(rows)} uncorrelated incidents for "
                f"service '{request.service}' in environment "
                f"'{request.environment.value}'; "
                f"at least {request.minimum_incidents} are required"
            )

        signals = [
            CorrelationSignal(
                anomaly_id=anomaly.id,
                incident_id=incident.id,
                rule_id=anomaly.rule_id,
                category=AnomalyCategory(anomaly.category),
                severity=AnomalySeverity(anomaly.severity),
                source=telemetry.source,
                observed_at=telemetry.observed_at,
            )
            for incident, anomaly, telemetry, _ in rows
        ]
        root_cause = self._analysis_engine.analyze(signals)

        incident_ids = [incident.id for incident, _, _, _ in rows]
        service = rows[0][3]
        created_at = datetime.now(UTC)
        summary = (
            f"Correlated {len(incident_ids)} incidents for "
            f"{request.service}/{request.environment.value}; "
            f"probable root cause is rule '{root_cause.rule_id}' "
            f"from source '{root_cause.source}'"
        )

        try:
            correlation = await self._repository.create(
                service_id=service.id,
                incident_ids=incident_ids,
                root_cause=root_cause,
                window_started_at=window_started_at,
                window_ended_at=window_ended_at,
                summary=summary,
                created_at=created_at,
            )
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

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
