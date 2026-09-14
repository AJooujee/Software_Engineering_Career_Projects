from fastapi.testclient import TestClient

from observability_platform.main import app

client = TestClient(app)


def test_health_endpoint_returns_healthy_status() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "observability-platform",
        "version": "0.1.0",
        "environment": "development",
    }


def test_openapi_schema_is_available() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == (
        "Observability & Incident Detection Platform"
    )
