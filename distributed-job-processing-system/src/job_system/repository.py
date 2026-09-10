import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from job_system.models import Job, JobStatus
from job_system.schemas import JobCreate


def add_job(session: AsyncSession, job_data: JobCreate) -> Job:
    """Add a new queued job to the current database transaction."""

    job = Job(
        queue=job_data.queue,
        task_name=job_data.task_name,
        payload=job_data.payload,
        priority=job_data.priority,
        status=JobStatus.QUEUED,
    )

    # SQLAlchemy tracks the object now, but no SQL is executed until flush/commit.
    session.add(job)
    return job


async def get_job_by_id(
    session: AsyncSession,
    job_id: uuid.UUID,
) -> Job | None:
    """Return one job by primary key, or None when it does not exist."""

    return await session.get(Job, job_id)


async def list_jobs(
    session: AsyncSession,
    *,
    queue: str | None = None,
    status: JobStatus | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Job]:
    """Return jobs with optional queue and status filters."""

    statement = select(Job)

    if queue is not None:
        statement = statement.where(Job.queue == queue)

    if status is not None:
        statement = statement.where(Job.status == status)

    # A secondary ID sort makes pagination deterministic when timestamps match.
    statement = statement.order_by(
        Job.created_at.desc(),
        Job.id.desc(),
    )
    statement = statement.limit(limit).offset(offset)

    result = await session.scalars(statement)
    return list(result.all())
