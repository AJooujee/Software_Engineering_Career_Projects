from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.routes.products import router as products_router
from app.api.routes.stock import router as stock_router

from app.core.observability import (
    RequestLoggingMiddleware,
    configure_logging,
)

SERVICE_NAME = "inventory-service"
configure_logging(SERVICE_NAME)

app = FastAPI(
    title="Inventory Service API",
    description="Manages products, inventory levels, and stock movements.",
    version="1.0.0",
)

app.add_middleware(
    RequestLoggingMiddleware,
    service_name=SERVICE_NAME,
)

app.include_router(products_router)
app.include_router(stock_router)


@app.get("/", tags=["General"])
def read_root() -> dict[str, str]:
    return {
        "message": "Inventory Service API",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "inventory-service",
    }


@app.get("/health/db", tags=["Health"])
def database_health_check(
    database: Session = Depends(get_db),
) -> dict[str, str]:
    database.execute(text("SELECT 1"))

    return {
        "status": "healthy",
        "database": "connected",
    }