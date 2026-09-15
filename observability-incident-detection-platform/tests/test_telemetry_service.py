import pytest

from observability_platform.schemas.telemetry import (
    MetricTelemetry,
    TelemetryBatch,
)
from observability_platform.services.telemetry_service import (
    InMemoryTelemetryStore,
)


def create_metric_batch(*values: float) -> TelemetryBatch:
    return TelemetryBatch(
        items=[
            MetricTelemetry(
                service="checkout-service",
                source="checkout-instance-1",
                name="cpu_usage",
                value=value,
                unit="percent",
            )
            for value in values
        ]
    )


@pytest.mark.asyncio
async def test_ingest_stores_telemetry_and_returns_ids() -> None:
    store = InMemoryTelemetryStore()
    batch = create_metric_batch(25.0, 50.0)

    result = await store.ingest(batch)

    assert result.accepted_count == 2
    assert len(result.telemetry_ids) == 2
    assert len(set(result.telemetry_ids)) == 2
    assert await store.count() == 2


@pytest.mark.asyncio
async def test_store_returns_ingested_items() -> None:
    store = InMemoryTelemetryStore()
    await store.ingest(create_metric_batch(72.5))

    stored_items = await store.list_items()

    assert len(stored_items) == 1
    assert isinstance(stored_items[0].data, MetricTelemetry)
    assert stored_items[0].data.value == 72.5
    assert stored_items[0].received_at.tzinfo is not None


@pytest.mark.asyncio
async def test_store_respects_maximum_size() -> None:
    store = InMemoryTelemetryStore(max_items=2)

    await store.ingest(create_metric_batch(10.0, 20.0, 30.0))

    stored_items = await store.list_items()

    assert await store.count() == 2
    assert [item.data.value for item in stored_items] == [20.0, 30.0]


@pytest.mark.asyncio
async def test_store_can_be_cleared() -> None:
    store = InMemoryTelemetryStore()
    await store.ingest(create_metric_batch(10.0))

    await store.clear()

    assert await store.count() == 0


def test_store_rejects_invalid_maximum_size() -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        InMemoryTelemetryStore(max_items=0)
