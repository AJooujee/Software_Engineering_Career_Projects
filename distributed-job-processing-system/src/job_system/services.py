import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from job_system.models import Job, JobStatus
from job_system.repository import add_job, get_job_by_id, list_jobs
from job_system.schemas import JobCreate


class JobService:
    """Coordinate job operations and database transaction boundaries."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_job(self, job_data: JobCreate) -> Job:
        # The transaction commits only when every operation inside succeeds.
        async with self._session.begin():
            job = add_job(self._session, job_data)
            await self._session.flush()

        # Refresh guarantees that database-generated timestamps are available.
        await self._session.refresh(job)
        return job

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
