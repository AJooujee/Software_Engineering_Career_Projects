"""Integration coverage for readiness and safe request correlation."""

import re
from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_db
from app.main import app


class FailingSession:
    """Minimal database stand-in that simulates an unavailable dependency."""

    def execute(self, *_args: object, **_kwargs: object) -> None:
        raise SQLAlchemyError("test-only internal database detail")


def failing_database() -> Generator[FailingSession, None, None]:
    """Provide a database dependency that fails its readiness query."""

    yield FailingSession()


def test_request_id_is_generated(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert re.fullmatch(
        r"[0-9a-f]{32}",
        response.headers["X-Request-ID"],
    )


def test_safe_request_id_is_preserved(client: TestClient) -> None:
    response = client.get(
        "/health",
        headers={"X-Request-ID": "phase9-test.request_123"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "phase9-test.request_123"


def test_unsafe_request_id_is_replaced(client: TestClient) -> None:
    response = client.get(
        "/health",
        headers={"X-Request-ID": "unsafe request id"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] != "unsafe request id"
    assert re.fullmatch(
        r"[0-9a-f]{32}",
        response.headers["X-Request-ID"],
    )


def test_readiness_checks_database(client: TestClient) -> None:
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "service": "cloud-operations-api",
        "database": "available",
    }
    assert response.headers["X-Request-ID"]


def test_readiness_failure_is_sanitized(client: TestClient) -> None:
    original_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = failing_database

    try:
        response = client.get("/health/ready")
    finally:
        if original_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = original_override

    assert response.status_code == 503
    assert response.json() == {"detail": "Database is unavailable."}
    assert "internal database detail" not in response.text
    assert response.headers["X-Request-ID"]
