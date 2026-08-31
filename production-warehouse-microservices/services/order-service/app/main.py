from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.routes import orders_router
from app.db.database import get_db


app = FastAPI(
    title="Order Service API",
    description=(
        "Manages customer orders and their inventory reservation lifecycle."
    ),
    version="1.0.0",
)

app.include_router(orders_router)


@app.get("/", tags=["General"])
def read_root() -> dict[str, str]:
    """Return basic service discovery information."""

    return {
        "message": "Order Service API",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """Report whether the API process is running."""

    return {
        "status": "healthy",
        "service": "order-service",
    }


@app.get("/health/db", tags=["Health"])
def database_health_check(
    database: Session = Depends(get_db),
) -> dict[str, str]:
    """Verify connectivity to the Order PostgreSQL database."""

    database.execute(text("SELECT 1"))

    return {
        "status": "healthy",
        "database": "connected",
    }