"""Integration tests for PostgreSQL-backed readiness checks."""

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock

import pytest
from httpx2 import AsyncClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from observability_platform.db.session import get_db_session
from observability_platform.main import app

pytestmark = pytest.mark.asyncio


async def test_database_health_returns_healthy(
    api_client: AsyncClient,
) -> None:
    """The legacy database endpoint should preserve its response contract."""

    # Act: execute the compatibility database-health check.
    response = await api_client.get("/health/db")

    # Assert: existing clients still receive the original healthy payload.
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "database": "postgresql",
    }
    assert "X-Request-ID" in response.headers


async def test_readiness_returns_ready_when_database_responds(
    api_client: AsyncClient,
) -> None:
    """Readiness should succeed when the required database accepts a query."""

    # Act: call readiness through the isolated SQLite integration session.
    response = await api_client.get("/health/ready")

    # Assert: the process is eligible to receive application traffic.
    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "database": "postgresql",
    }
    assert response.headers["Cache-Control"] == "no-store"
    assert "X-Request-ID" in response.headers


async def test_readiness_returns_service_unavailable_on_database_error(
    api_client: AsyncClient,
) -> None:
    """Readiness should fail closed when database connectivity is lost."""

    # Arrange: preserve the working fixture override so it can be restored after
    # replacing the session with one that raises a SQLAlchemy connectivity error.
    original_override = app.dependency_overrides[get_db_session]
    failing_session = AsyncMock(spec=AsyncSession)
    failing_session.execute.side_effect = SQLAlchemyError("database unavailable")

    async def override_failed_db_session() -> AsyncIterator[AsyncSession]:
        """Yield the deterministic failing session for this request only."""

        yield failing_session

    app.dependency_overrides[get_db_session] = override_failed_db_session

    try:
        # Act: execute the readiness query against the failing session.
        response = await api_client.get("/health/ready")
    finally:
        # Restore the fixture-managed session override for test isolation.
        app.dependency_overrides[get_db_session] = original_override

    # Assert: orchestrators receive an explicit temporary-unavailability signal.
    assert response.status_code == 503
    assert response.json() == {
        "detail": "Database connection failed",
    }
    assert response.headers["Cache-Control"] == "no-store"
    assert "X-Request-ID" in response.headers
