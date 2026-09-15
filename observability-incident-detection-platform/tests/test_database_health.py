import pytest
from httpx2 import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_database_health_returns_healthy(
    api_client: AsyncClient,
) -> None:
    response = await api_client.get("/health/db")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "database": "postgresql",
    }
    assert "X-Request-ID" in response.headers
