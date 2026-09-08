from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

from job_system import __version__


class ServiceInfo(BaseModel):
    service: str
    version: str
    documentation: str


class HealthResponse(BaseModel):
    status: Literal["healthy"]
    service: str
    version: str


app = FastAPI(
    title="Distributed Job Processing System",
    description=(
        "A distributed job queue with concurrent workers, retries, "
        "idempotency, and fault recovery."
    ),
    version=__version__,
)


@app.get("/", response_model=ServiceInfo, tags=["System"])
async def service_info() -> ServiceInfo:
    return ServiceInfo(
        service="distributed-job-processing-system",
        version=__version__,
        documentation="/docs",
    )


@app.get("/health/live", response_model=HealthResponse, tags=["System"])
async def liveness_check() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        service="distributed-job-processing-system",
        version=__version__,
    )