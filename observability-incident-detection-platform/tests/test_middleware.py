from uuid import UUID

from fastapi.testclient import TestClient

from observability_platform.main import app

client = TestClient(app)


def test_response_contains_generated_request_id() -> None:
    response = client.get("/health")

    request_id = response.headers["X-Request-ID"]

    assert response.status_code == 200
    assert UUID(request_id).version == 4


def test_existing_request_id_is_preserved() -> None:
    request_id = "test-request-123"

    response = client.get(
        "/health",
        headers={"X-Request-ID": request_id},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id
