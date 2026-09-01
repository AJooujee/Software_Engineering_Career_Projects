from uuid import UUID

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_request_id_is_preserved() -> None:
    """Return a caller-provided request ID unchanged."""

    response = client.get(
        "/health",
        headers={"X-Request-ID": "test-request-123"},
    )

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "test-request-123"


def test_request_id_is_generated() -> None:
    """Generate a valid request ID when the caller omits one."""

    response = client.get("/health")

    assert response.status_code == 200

    generated_request_id = response.headers["x-request-id"]

    UUID(generated_request_id)