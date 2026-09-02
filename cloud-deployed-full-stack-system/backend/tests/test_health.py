"""Automated tests for the Cloud Operations system endpoints."""

from fastapi.testclient import TestClient

from app.main import app


# Create an in-memory client without starting an external Uvicorn server.
client = TestClient(app)


def test_health_check() -> None:
    """Verify that the health endpoint returns the expected service status."""

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "cloud-operations-api",
    }


def test_local_frontend_origin_is_allowed() -> None:
    """Verify that the local React application is permitted by CORS."""

    frontend_origin = "http://127.0.0.1:5173"

    response = client.get(
        "/health",
        headers={"Origin": frontend_origin},
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == frontend_origin