from fastapi import FastAPI

from observability_platform.api.routes.telemetry import router as telemetry_router
from observability_platform.config import get_settings
from observability_platform.logging_config import configure_logging
from observability_platform.middleware import RequestIDMiddleware

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title=settings.app_name,
    description="API for monitoring services and detecting operational incidents.",
    version=settings.app_version,
)

app.add_middleware(RequestIDMiddleware)
app.include_router(telemetry_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "observability-platform",
        "version": settings.app_version,
        "environment": settings.environment,
    }
