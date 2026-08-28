from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.routes.warehouses import router as warehouses_router


app = FastAPI(
    title="Warehouse Service API",
    description=(
        "Manages warehouse locations and coordinates stock transfers "
        "between warehouses."
    ),
    version="1.0.0",
)

app.include_router(warehouses_router)


@app.get("/", tags=["General"])
def read_root() -> dict[str, str]:
    """Return basic service information and the documentation location."""
    return {
        "message": "Warehouse Service API",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """Provide a lightweight health check without accessing PostgreSQL."""
    return {
        "status": "healthy",
        "service": "warehouse-service",
    }


@app.get("/health/db", tags=["Health"])
def database_health_check(
    database: Session = Depends(get_db),
) -> dict[str, str]:
    """Verify that the service can execute a query against PostgreSQL."""
    database.execute(text("SELECT 1"))

    return {
        "status": "healthy",
        "database": "connected",
    }