from httpx2 import AsyncClient


async def test_service_info(client: AsyncClient) -> None:
    response = await client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "service": "distributed-job-processing-system",
        "version": "1.0.0",
        "documentation": "/docs",
    }


async def test_liveness_check(client: AsyncClient) -> None:
    response = await client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "distributed-job-processing-system",
        "version": "1.0.0",
    }


async def test_metrics_endpoint(client: AsyncClient) -> None:
    response = await client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "# HELP job_system_jobs_submitted_total" in response.text
    assert "# TYPE job_system_job_processing_seconds histogram" in response.text


async def test_response_preserves_valid_request_id(
    client: AsyncClient,
) -> None:
    response = await client.get(
        "/health/live",
        headers={"X-Request-ID": "phase8-request-123"},
    )

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "phase8-request-123"
    assert response.headers["x-content-type-options"] == "nosniff"


async def test_response_replaces_invalid_request_id(
    client: AsyncClient,
) -> None:
    response = await client.get(
        "/health/live",
        headers={"X-Request-ID": "contains spaces"},
    )

    request_id = response.headers["x-request-id"]

    assert response.status_code == 200
    assert request_id != "contains spaces"
    assert len(request_id) == 32
    assert request_id.isalnum()
