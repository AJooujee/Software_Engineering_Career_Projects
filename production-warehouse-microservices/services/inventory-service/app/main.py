from fastapi import FastAPI

app = FastAPI(
    title="Inventory Service API",
    description="Manages products, inventory levels, and stock movements.",
    version="1.0.0",
)


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