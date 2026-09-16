from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

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
from observability_platform.middleware import RequestIDMiddleware

settings = get_settings()
configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await close_database_connection()


app = FastAPI(
    title=settings.app_name,
    description="API for monitoring services and detecting operational incidents.",
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(RequestIDMiddleware)
app.include_router(anomalies_router)
app.include_router(health_router)
app.include_router(incidents_router)
app.include_router(services_router)
app.include_router(correlations_router)
app.include_router(telemetry_router)
app.include_router(traces_router)
app.include_router(dashboard_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "observability-platform",
        "version": settings.app_version,
        "environment": settings.environment,
    }
