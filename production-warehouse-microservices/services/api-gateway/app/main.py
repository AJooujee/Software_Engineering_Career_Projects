from fastapi import FastAPI

from app.api.routes import router as gateway_router
from app.core.config import get_settings
from app.core.observability import (
    RequestLoggingMiddleware,
    configure_logging,
)


settings = get_settings()
configure_logging(settings.service_name)

app = FastAPI(
    title="Warehouse Platform API Gateway",
    version="1.0.0",
    description=(
        "Single entry point for the Inventory, Warehouse, and Order services."
    ),
)

app.add_middleware(
    RequestLoggingMiddleware,
    service_name=settings.service_name,
)

app.include_router(gateway_router)


@app.get("/", tags=["System"])
def read_root() -> dict[str, str]:
    """Describe the API Gateway entry point."""

    return {
        "service": settings.service_name,
        "message": "Warehouse platform API Gateway is running",
    }


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    """Report whether the Gateway process is running."""

    return {
        "status": "healthy",
        "service": settings.service_name,
    }