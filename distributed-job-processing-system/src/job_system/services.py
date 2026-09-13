import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from job_system.models import Job, JobStatus
from job_system.repository import (
    create_or_get_idempotent_job,
    get_job_by_id,
    list_jobs,
)
from job_system.schemas import JobCreate


@dataclass(frozen=True, slots=True)
class JobSubmissionResult:
    """Describe the stored job and whether this request created it."""

    job: Job
    created: bool


class IdempotencyConflictError(Exception):
    """Raised when one idempotency key is reused for different work."""


def job_matches_submission(job: Job, job_data: JobCreate) -> bool:
    """Check whether an existing job represents the repeated submission."""

    return (
        job.queue == job_data.queue
        and job.task_name == job_data.task_name
        and job.payload == job_data.payload
        and job.priority == job_data.priority
        and job.max_attempts == job_data.max_attempts
    )


class JobService:
    """Coordinate job operations and database transaction boundaries."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_job(
        self,
        job_data: JobCreate,
    ) -> JobSubmissionResult:
        """Create a job or safely reuse an idempotent submission."""

        async with self._session.begin():
            job, created = await create_or_get_idempotent_job(
                self._session,
                job_data,
            )

            if not created and not job_matches_submission(job, job_data):
                raise IdempotencyConflictError(
                    "Idempotency key is already associated with a different job submission"
                )

        # Refresh guarantees that database-generated fields are available.
        await self._session.refresh(job)
        return JobSubmissionResult(
            job=job,
            created=created,
        )

    async def get_job(self, job_id: uuid.UUID) -> Job | None:
        return await get_job_by_id(self._session, job_id)

    async def get_jobs(
        self,
        *,
        queue: str | None = None,
        status: JobStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Job]:
        return await list_jobs(
            self._session,
            queue=queue,
            status=status,
            limit=limit,
            offset=offset,
        )
