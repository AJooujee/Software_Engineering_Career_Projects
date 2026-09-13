from httpx2 import AsyncClient


async def test_service_info(client: AsyncClient) -> None:
    response = await client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "service": "distributed-job-processing-system",
        "version": "0.7.0",
        "documentation": "/docs",
    }


async def test_liveness_check(client: AsyncClient) -> None:
    response = await client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "distributed-job-processing-system",
        "version": "0.7.0",
    }


async def test_metrics_endpoint(client: AsyncClient) -> None:
    response = await client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "# HELP job_system_jobs_submitted_total" in response.text
    assert "# TYPE job_system_job_processing_seconds histogram" in response.text
