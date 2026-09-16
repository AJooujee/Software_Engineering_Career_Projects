"""Database operations for telemetry ingestion and query workflows."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from observability_platform.db.models import MonitoredService, TelemetryRecord
from observability_platform.schemas.telemetry import TelemetryItem

# Return telemetry and service data together so upper layers can construct
# responses without issuing one service query for every telemetry record.
TelemetryRow = tuple[TelemetryRecord, MonitoredService]


class TelemetryRepository:
    """Persist telemetry batches and execute filtered telemetry queries."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind repository operations to the caller's database transaction."""

        # Commit and rollback remain responsibilities of the service layer.
        self._session = session

    async def create_batch(
        self,
        items: list[tuple[TelemetryItem, UUID]],
        *,
        received_at: datetime,
    ) -> list[TelemetryRecord]:
        """Build and flush persistent records for a telemetry batch."""

        # Convert validated telemetry schemas into ORM records while preserving
        # each resolved service foreign key.
        records = [
            TelemetryRecord(
                # Generate an internal database identity for every observation.
                id=uuid4(),
                service_id=service_id,
                # Store shared indexed fields separately from the flexible JSON
                # payload so common queries do not require JSON extraction.
                telemetry_type=item.type,
                source=item.source,
                observed_at=item.timestamp,
                received_at=received_at,
                # Preserve the complete validated telemetry item for
                # type-specific fields such as metric name, value, and unit.
                payload=item.model_dump(mode="json"),
            )
            for item, service_id in items
        ]

        # Flush as one batch while leaving transaction completion to the
        # application service.
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
    ) -> tuple[list[TelemetryRow], int]:
        """Query telemetry records with filters and offset pagination."""

        # Build one shared filter list for both count and result queries.
        filters = []

        # Apply service registry filters only when clients supply them.
        if service is not None:
            filters.append(MonitoredService.name == service)
        if environment is not None:
            filters.append(MonitoredService.environment == environment)

        # Apply telemetry-specific filters to indexed record columns.
        if telemetry_type is not None:
            filters.append(TelemetryRecord.telemetry_type == telemetry_type)
        if source is not None:
            filters.append(TelemetryRecord.source == source)

        # Use inclusive time boundaries so records exactly on either boundary
        # remain visible in deterministic time-range queries.
        if observed_from is not None:
            filters.append(TelemetryRecord.observed_at >= observed_from)
        if observed_to is not None:
            filters.append(TelemetryRecord.observed_at <= observed_to)

        # Count all matching rows independently from page size and offset.
        count_statement = (
            select(func.count())
            .select_from(TelemetryRecord)
            .join(
                MonitoredService,
                MonitoredService.id == TelemetryRecord.service_id,
            )
            .where(*filters)
        )
        total = (await self._session.execute(count_statement)).scalar_one()

        # Load one page with service identity included in every result row.
        query_statement = (
            select(TelemetryRecord, MonitoredService)
            .select_from(TelemetryRecord)
            .join(
                MonitoredService,
                MonitoredService.id == TelemetryRecord.service_id,
            )
            .where(*filters)
            .order_by(
                # General telemetry queries present the newest observations
                # first, with UUID ordering as a stable timestamp tie-breaker.
                TelemetryRecord.observed_at.desc(),
                TelemetryRecord.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(query_statement)

        # Materialize SQLAlchemy rows into a predictable repository return type.
        rows = [
            (record, monitored_service) for record, monitored_service in result.all()
        ]

        return rows, total

    async def query_metric_records(
        self,
        *,
        service: str,
        environment: str,
        source: str | None,
        observed_from: datetime,
        observed_to: datetime,
    ) -> list[TelemetryRow]:
        """Load metric records for one service inside a bounded time window."""

        # Always constrain dashboard queries to metric telemetry and a specific
        # service identity so logs and events never enter numeric aggregation.
        filters = [
            TelemetryRecord.telemetry_type == "metric",
            MonitoredService.name == service,
            MonitoredService.environment == environment,
            TelemetryRecord.observed_at >= observed_from,
            TelemetryRecord.observed_at <= observed_to,
        ]

        # Source remains optional so dashboards can aggregate either one
        # runtime instance or every instance belonging to the service.
        if source is not None:
            filters.append(TelemetryRecord.source == source)

        # Metric names live in the JSON payload. Filtering them in the service
        # layer keeps this repository query portable across PostgreSQL and the
        # SQLite integration-test database.
        statement = (
            select(TelemetryRecord, MonitoredService)
            .select_from(TelemetryRecord)
            .join(
                MonitoredService,
                MonitoredService.id == TelemetryRecord.service_id,
            )
            .where(*filters)
            .order_by(
                # Dashboard points are returned oldest first for charting.
                TelemetryRecord.observed_at,
                TelemetryRecord.id,
            )
        )
        result = await self._session.execute(statement)

        return [
            (record, monitored_service) for record, monitored_service in result.all()
        ]
