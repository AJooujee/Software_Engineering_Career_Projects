import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from observability_platform.db.models import TelemetryRecord
from observability_platform.schemas.service import (
    ServiceCreate,
    ServiceEnvironment,
)
from observability_platform.schemas.telemetry import (
    MetricTelemetry,
    TelemetryBatch,
)
from observability_platform.services.persistent_telemetry_service import (
    PersistentTelemetryService,
    UnregisteredServiceError,
)
from observability_platform.services.service_registry import (
    ServiceRegistryService,
)

pytestmark = pytest.mark.asyncio


async def register_service(
    session: AsyncSession,
    *,
    name: str = "checkout-service",
    environment: ServiceEnvironment = ServiceEnvironment.DEVELOPMENT,
) -> None:
    registry = ServiceRegistryService(session)
    await registry.register(
        ServiceCreate(
            name=name,
            environment=environment,
        )
    )


def create_metric_batch(
    *values: float,
    service: str = "checkout-service",
    environment: ServiceEnvironment = ServiceEnvironment.DEVELOPMENT,
) -> TelemetryBatch:
    return TelemetryBatch(
        items=[
            MetricTelemetry(
                service=service,
                environment=environment,
                source="checkout-instance-1",
                name="cpu_usage",
                value=value,
                unit="percent",
            )
            for value in values
        ]
    )


async def test_ingest_persists_telemetry_records(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with test_session_factory() as session:
        await register_service(session)
        service = PersistentTelemetryService(session)

        result = await service.ingest(create_metric_batch(25.0, 50.0))
        query_result = await session.execute(select(TelemetryRecord))
        records = list(query_result.scalars().all())

    assert result.accepted_count == 2
    assert len(records) == 2
    assert records[0].payload["name"] == "cpu_usage"
    assert records[0].payload["value"] == 25.0


async def test_ingest_returns_unique_telemetry_ids(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with test_session_factory() as session:
        await register_service(session)
        service = PersistentTelemetryService(session)

        result = await service.ingest(create_metric_batch(10.0, 20.0))

    assert len(result.telemetry_ids) == 2
    assert len(set(result.telemetry_ids)) == 2


async def test_ingest_rejects_unregistered_service(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with test_session_factory() as session:
        service = PersistentTelemetryService(session)

        with pytest.raises(
            UnregisteredServiceError,
            match="not registered",
        ):
            await service.ingest(create_metric_batch(10.0))


async def test_rejected_batch_does_not_store_partial_records(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with test_session_factory() as session:
        await register_service(session)
        service = PersistentTelemetryService(session)
        batch = TelemetryBatch(
            items=[
                *create_metric_batch(10.0).items,
                *create_metric_batch(
                    20.0,
                    service="unknown-service",
                ).items,
            ]
        )

        with pytest.raises(UnregisteredServiceError):
            await service.ingest(batch)

        count_result = await session.execute(
            select(func.count()).select_from(TelemetryRecord)
        )

    assert count_result.scalar_one() == 0


async def test_same_service_name_supports_multiple_environments(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with test_session_factory() as session:
        await register_service(
            session,
            environment=ServiceEnvironment.DEVELOPMENT,
        )
        await register_service(
            session,
            environment=ServiceEnvironment.STAGING,
        )

        service = PersistentTelemetryService(session)
        batch = TelemetryBatch(
            items=[
                *create_metric_batch(
                    10.0,
                    environment=ServiceEnvironment.DEVELOPMENT,
                ).items,
                *create_metric_batch(
                    20.0,
                    environment=ServiceEnvironment.STAGING,
                ).items,
            ]
        )

        result = await service.ingest(batch)
        service_ids_result = await session.execute(select(TelemetryRecord.service_id))
        service_ids = set(service_ids_result.scalars().all())

    assert result.accepted_count == 2
    assert len(service_ids) == 2
