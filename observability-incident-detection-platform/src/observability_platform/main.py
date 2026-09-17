"""FastAPI application assembly and lifecycle management."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from starlette.middleware.trustedhost import TrustedHostMiddleware

from observability_platform.api.routes.anomalies import (
    router as anomalies_router,
)
from observability_platform.api.routes.correlations import (
    router as correlations_router,
)
from observability_platform.api.routes.dashboard import (
    router as dashboard_router,
)
from observability_platform.api.routes.health import router as health_router
from observability_platform.api.routes.incidents import (
    router as incidents_router,
)
from observability_platform.api.routes.services import router as services_router
from observability_platform.api.routes.telemetry import (
    router as telemetry_router,
)
from observability_platform.api.routes.traces import router as traces_router
from observability_platform.config import get_settings
from observability_platform.db.session import close_database_connection
from observability_platform.logging_config import configure_logging
from observability_platform.middleware import (
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
)
from observability_platform.rate_limit import RateLimitMiddleware
from observability_platform.security import require_api_key

# Load and validate configuration before accepting requests. Invalid production
# settings therefore stop the process during startup instead of failing later.
settings = get_settings()

# Configure structured logging once with the validated runtime log level.
configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Manage resources shared across the application process."""

    # The application currently has no asynchronous startup resource to create.
    yield

    # Dispose pooled database connections during graceful shutdown.
    await close_database_connection()


# Build the API with metadata sourced from validated settings.
app = FastAPI(
    title=settings.app_name,
    description="API for monitoring services and detecting operational incidents.",
    version=settings.app_version,
    lifespan=lifespan,
)

# Apply one client-wide allowance across protected business endpoints. This
# middleware is registered inside trusted-host validation so rejected Host
# headers do not consume a legitimate client's request allowance.
app.add_middleware(
    RateLimitMiddleware,
    enabled=settings.rate_limit_enabled,
    request_limit=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
)

# Reject unexpected Host headers before requests reach business routes.
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.trusted_hosts,
)

# Request IDs correlate successful and failed requests with structured logs.
app.add_middleware(RequestIDMiddleware)

# Security headers wrap the complete request pipeline, including errors emitted
# by trusted-host validation. HSTS is enabled only for production deployments.
app.add_middleware(
    SecurityHeadersMiddleware,
    enable_hsts=settings.environment == "production",
)

# Health endpoints intentionally remain public. Container orchestrators and
# load balancers must be able to check liveness and database readiness without
# storing or transmitting application credentials.
app.include_router(health_router)

# Reuse one dependency declaration across every business router. The dependency
# becomes a no-op when authentication is disabled in local development.
protected_dependencies = [Depends(require_api_key)]

app.include_router(
    anomalies_router,
    dependencies=protected_dependencies,
)
app.include_router(
    correlations_router,
    dependencies=protected_dependencies,
)
app.include_router(
    dashboard_router,
    dependencies=protected_dependencies,
)
app.include_router(
    incidents_router,
    dependencies=protected_dependencies,
)
app.include_router(
    services_router,
    dependencies=protected_dependencies,
)
app.include_router(
    telemetry_router,
    dependencies=protected_dependencies,
)
app.include_router(
    traces_router,
    dependencies=protected_dependencies,
)


@app.get(
    "/health",
    tags=["Health"],
    summary="Check application liveness",
)
async def health_check() -> dict[str, str]:
    """Return process-level health without accessing external dependencies."""

    return {
        "status": "healthy",
        "service": "observability-platform",
        "version": settings.app_version,
        "environment": settings.environment,
    }
