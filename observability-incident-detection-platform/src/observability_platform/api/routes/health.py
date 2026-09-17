"""Public liveness and database-readiness endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from observability_platform.db.session import get_db_session

# Health routes remain outside API-key authentication so infrastructure can
# evaluate the service without storing application credentials.
router = APIRouter(tags=["Health"])

# Reuse the normal request-scoped database session for readiness checks. This
# also keeps integration tests isolated through the existing dependency override.
SessionDependency = Annotated[AsyncSession, Depends(get_db_session)]


async def verify_database_readiness(
    session: AsyncSession,
) -> None:
    """Raise HTTP 503 when PostgreSQL cannot answer a lightweight query."""

    try:
        # SELECT 1 verifies connectivity without depending on application data.
        await session.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        # A 503 tells load balancers not to route traffic to this process while
        # preserving the distinction from an application programming error.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed",
        ) from error


@router.get(
    "/health/live",
    summary="Check application liveness",
)
async def liveness_health() -> dict[str, str]:
    """Confirm that the API process can receive and handle HTTP requests."""

    # Liveness intentionally avoids database access. Restarting a healthy
    # process cannot repair an unavailable external database.
    return {
        "status": "healthy",
        "check": "liveness",
    }


@router.get(
    "/health/ready",
    summary="Check application readiness",
)
async def readiness_health(
    session: SessionDependency,
) -> dict[str, str]:
    """Confirm that the process and required database are ready for traffic."""

    # Readiness succeeds only after the required PostgreSQL dependency responds.
    await verify_database_readiness(session)

    return {
        "status": "ready",
        "database": "postgresql",
    }


@router.get(
    "/health/db",
    summary="Check database connectivity",
)
async def database_health(
    session: SessionDependency,
) -> dict[str, str]:
    """Preserve the original database-health contract for existing clients."""

    # This compatibility endpoint uses the same readiness implementation while
    # retaining the response body documented in earlier project phases.
    await verify_database_readiness(session)

    return {
        "status": "healthy",
        "database": "postgresql",
    }
