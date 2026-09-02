"""Application entry point for the Cloud Operations backend API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


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


# Allow the local React application to communicate with the FastAPI backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=LOCAL_FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["System"])
def read_root() -> dict[str, str]:
    """Return a basic message confirming that the API is available."""

    return {
        "message": "Cloud Operations API is running",
    }


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    """Return the current health status of the backend service."""

    return {
        "status": "healthy",
        "service": "cloud-operations-api",
    }