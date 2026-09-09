from httpx2 import AsyncClient


async def test_service_info(client: AsyncClient) -> None:
    response = await client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "service": "distributed-job-processing-system",
        "version": "0.2.0",
        "documentation": "/docs",
    }


async def test_liveness_check(client: AsyncClient) -> None:
    response = await client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "distributed-job-processing-system",
        "version": "0.2.0",
    }
