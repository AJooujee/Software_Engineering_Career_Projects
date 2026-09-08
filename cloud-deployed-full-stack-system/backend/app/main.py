"""Application entry point for the Cloud Operations backend API."""

from time import perf_counter

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.routes import (
    audit_events_router,
    auth_router,
    dashboard_router,
    incidents_router,
    users_router,
)
from app.core.observability import configure_request_logger, resolve_request_id
from app.db.session import get_db


# Frontend addresses permitted to call the API during local development.
LOCAL_FRONTEND_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]


app = FastAPI(
    title="Cloud Operations API",
    description="Backend API for the Cloud Operations and Incident Management Platform",
    version="0.1.0",
)
request_logger = configure_request_logger()


# Allow the local React application to communicate with the FastAPI backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=LOCAL_FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


@app.middleware("http")
async def record_request(request: Request, call_next):
    """Attach a correlation ID and emit one safe structured request event."""

    request_id = resolve_request_id(request.headers.get("X-Request-ID"))
    request.state.request_id = request_id
    started_at = perf_counter()
    fields: dict[str, object] = {
        "request_id": request_id,
        "method": request.method,
        # Deliberately omit query strings, bodies, credentials, and client IPs.
        "path": request.url.path,
    }

    try:
        response = await call_next(request)
    except Exception as error:
        fields["status_code"] = status.HTTP_500_INTERNAL_SERVER_ERROR
        fields["duration_ms"] = round(
            (perf_counter() - started_at) * 1000,
            2,
        )
        fields["error_type"] = type(error).__name__
        request_logger.error("request_failed", extra=fields)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error."},
            headers={"X-Request-ID": request_id},
        )

    fields["status_code"] = response.status_code
    fields["duration_ms"] = round(
        (perf_counter() - started_at) * 1000,
        2,
    )
    response.headers["X-Request-ID"] = request_id
    request_logger.info("request_completed", extra=fields)
    return response


@app.get("/", tags=["System"])
def read_root() -> dict[str, str]:
    """Return a basic message confirming that the API is available."""

    return {
        "message": "Cloud Operations API is running",
    }


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    """Return process liveness without depending on another service."""

    return {
        "status": "healthy",
        "service": "cloud-operations-api",
    }


@app.get("/health/ready", tags=["System"])
def readiness_check(
    database: Session = Depends(get_db),
) -> dict[str, str]:
    """Report whether the API can execute a minimal database query."""

    try:
        database.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        ) from error

    return {
        "status": "ready",
        "service": "cloud-operations-api",
        "database": "available",
    }


# Register administrator audit-history endpoints.
app.include_router(audit_events_router, prefix="/api")

# Register authenticated dashboard endpoints under the shared API prefix.
app.include_router(dashboard_router, prefix="/api")

# Register incident endpoints under the shared API prefix.
app.include_router(incidents_router, prefix="/api")

# Register authentication endpoints under the shared API prefix.
app.include_router(auth_router, prefix="/api")

# Register administrator user-management endpoints.
app.include_router(users_router, prefix="/api")
