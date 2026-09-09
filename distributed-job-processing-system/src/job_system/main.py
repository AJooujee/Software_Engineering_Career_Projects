from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi import status as http_status
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from job_system import __version__
from job_system.api.jobs import router as jobs_router
from job_system.db import check_database_connection, close_database_connection


class ServiceInfo(BaseModel):
    service: str
    version: str
    documentation: str


class HealthResponse(BaseModel):
    status: Literal["healthy"]
    service: str
    version: str


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Release database connections during graceful application shutdown."""

    yield
    await close_database_connection()


app = FastAPI(
    title="Distributed Job Processing System",
    description=(
        "A distributed job queue with concurrent workers, retries, idempotency, and fault recovery."
    ),
    version=__version__,
    lifespan=lifespan,
)

# Keep job endpoints in a separate router as the application grows.
app.include_router(jobs_router)


@app.get("/", response_model=ServiceInfo, tags=["System"])
async def service_info() -> ServiceInfo:
    return ServiceInfo(
        service="distributed-job-processing-system",
        version=__version__,
        documentation="/docs",
    )


@app.get("/health/live", response_model=HealthResponse, tags=["System"])
async def liveness_check() -> HealthResponse:
    """Confirm that the API process is running."""

    return HealthResponse(
        status="healthy",
        service="distributed-job-processing-system",
        version=__version__,
    )


@app.get(
    "/health/ready",
    response_model=HealthResponse,
    tags=["System"],
    responses={
        http_status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "PostgreSQL is unavailable"}
    },
)
async def readiness_check() -> HealthResponse:
    """Confirm that the API can communicate with PostgreSQL."""

    try:
        connected = await check_database_connection()
    except (SQLAlchemyError, OSError) as error:
        raise HTTPException(
            status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        ) from error

    if not connected:
        raise HTTPException(
            status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database readiness check failed",
        )

    return HealthResponse(
        status="healthy",
        service="distributed-job-processing-system",
        version=__version__,
    )
