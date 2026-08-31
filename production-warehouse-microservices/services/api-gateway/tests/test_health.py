from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_endpoint() -> None:
    """Verify the Gateway root response."""

    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "service": "api-gateway",
        "message": "Warehouse platform API Gateway is running",
    }


def test_health_check() -> None:
    """Verify the Gateway process health response."""

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "api-gateway",
    }