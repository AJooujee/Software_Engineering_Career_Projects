from collections.abc import AsyncIterator

import pytest
from httpx2 import ASGITransport, AsyncClient

from job_system.main import app


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as test_client:
        yield test_client


async def test_service_info(client: AsyncClient) -> None:
    response = await client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "service": "distributed-job-processing-system",
        "version": "0.1.0",
        "documentation": "/docs",
    }


async def test_liveness_check(client: AsyncClient) -> None:
    response = await client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "distributed-job-processing-system",
        "version": "0.1.0",
    }