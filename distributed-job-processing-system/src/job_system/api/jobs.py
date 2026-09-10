import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from job_system.db import get_session
from job_system.models import JobStatus
from job_system.schemas import JobCreate, JobRead
from job_system.services import JobService

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
)


async def get_job_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> JobService:
    """Create a job service using one database session per API request."""

    return JobService(session)


JobServiceDependency = Annotated[
    JobService,
    Depends(get_job_service),
]


@router.post(
    "",
    response_model=JobRead,
    status_code=http_status.HTTP_201_CREATED,
)
async def create_job(
    job_data: JobCreate,
    service: JobServiceDependency,
) -> JobRead:
    """Persist a new job with queued status."""

    job = await service.create_job(job_data)
    return JobRead.model_validate(job)


@router.get(
    "",
    response_model=list[JobRead],
)
async def get_jobs(
    service: JobServiceDependency,
    queue: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=100,
            pattern=r"^[A-Za-z0-9_.-]+$",
        ),
    ] = None,
    job_status: Annotated[
        JobStatus | None,
        Query(alias="status"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[JobRead]:
    """List jobs with filtering and pagination."""

    jobs = await service.get_jobs(
        queue=queue,
        status=job_status,
        limit=limit,
        offset=offset,
    )

    return [JobRead.model_validate(job) for job in jobs]


@router.get(
    "/{job_id}",
    response_model=JobRead,
)
async def get_job(
    job_id: uuid.UUID,
    service: JobServiceDependency,
) -> JobRead:
    """Return a single job or respond with HTTP 404."""

    job = await service.get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    return JobRead.model_validate(job)
