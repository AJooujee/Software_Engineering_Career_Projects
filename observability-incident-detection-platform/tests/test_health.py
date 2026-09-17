"""Tests for public process-liveness and OpenAPI endpoints."""

from fastapi.testclient import TestClient

from observability_platform.main import app

# TestClient uses the trusted ``testserver`` host configured for local tests.
client = TestClient(app)


def test_health_endpoint_returns_healthy_status() -> None:
    """The original health endpoint should remain backward compatible."""

    # Act: request the legacy process-health endpoint.
    response = client.get("/health")

    # Assert: existing clients continue receiving application metadata.
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "observability-platform",
        "version": "0.1.0",
        "environment": "development",
    }


def test_explicit_liveness_endpoint_does_not_require_database() -> None:
    """The liveness endpoint should report only process availability."""

    # Act: request the explicit orchestration-friendly endpoint.
    response = client.get("/health/live")

    # Assert: the response is public, lightweight, and clearly identified.
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "check": "liveness",
    }
    assert response.headers["Cache-Control"] == "no-store"
    assert "X-Request-ID" in response.headers


def test_openapi_schema_is_available() -> None:
    """Development environments should expose generated API documentation."""

    # Act: request the generated OpenAPI document.
    response = client.get("/openapi.json")

    # Assert: application metadata remains present in the schema.
    assert response.status_code == 200
    assert response.json()["info"]["title"] == (
        "Observability & Incident Detection Platform"
    )
