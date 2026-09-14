import re
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi import status as http_status
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from job_system import __version__
from job_system.api.jobs import router as jobs_router
from job_system.db import check_database_connection, close_database_connection
from job_system.observability import configure_logging, render_metrics

REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


def resolve_request_id(candidate: str | None) -> str:
    """Reuse a safe client request ID or generate a new identifier."""

    if candidate is not None and REQUEST_ID_PATTERN.fullmatch(candidate):
        return candidate

    return uuid4().hex


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

    configure_logging()
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


@app.middleware("http")
async def add_request_context(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Attach request correlation and basic security headers."""

    request_id = resolve_request_id(
        request.headers.get("X-Request-ID"),
    )
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


# Keep job endpoints in a separate router as the application grows.
app.include_router(jobs_router)


@app.get(
    "/metrics",
    response_class=Response,
    include_in_schema=False,
)
async def metrics() -> Response:
    """Expose application metrics in Prometheus text format."""

    content, content_type = render_metrics()
    return Response(
        content=content,
        headers={"Content-Type": content_type},
    )


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
