import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from job_system.models import Job, JobStatus


class PostgresJobQueue:
    """Coordinate atomic job claims and worker-owned status updates."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._session_factory = session_factory

    async def claim_jobs(
        self,
        *,
        worker_id: str,
        queues: tuple[str, ...],
        limit: int,
    ) -> list[Job]:
        """Atomically claim queued jobs for one worker process."""

        if not queues or limit < 1:
            return []

        async with self._session_factory() as session:
            async with session.begin():
                statement = (
                    select(Job)
                    .where(
                        Job.status == JobStatus.QUEUED,
                        Job.queue.in_(queues),
                    )
                    .order_by(
                        Job.priority.desc(),
                        Job.created_at.asc(),
                        Job.id.asc(),
                    )
                    # Locked rows are skipped instead of blocking other workers.
                    .with_for_update(skip_locked=True)
                    .limit(limit)
                )

                result = await session.scalars(statement)
                jobs = list(result.all())
                claimed_at = datetime.now(UTC)

                # The row locks remain held until all status changes are committed.
                for job in jobs:
                    job.status = JobStatus.RUNNING
                    job.worker_id = worker_id
                    job.attempt_count += 1
                    job.started_at = claimed_at
                    job.completed_at = None
                    job.result = None
                    job.last_error = None
                    job.updated_at = claimed_at

                await session.flush()

        return jobs

    async def mark_succeeded(
        self,
        *,
        job_id: uuid.UUID,
        worker_id: str,
        result_payload: dict[str, Any],
    ) -> bool:
        """Complete a job only when it is still owned by this worker."""

        completed_at = datetime.now(UTC)

        async with self._session_factory() as session:
            async with session.begin():
                statement = (
                    update(Job)
                    .where(
                        Job.id == job_id,
                        Job.status == JobStatus.RUNNING,
                        Job.worker_id == worker_id,
                    )
                    .values(
                        status=JobStatus.SUCCEEDED,
                        result=result_payload,
                        last_error=None,
                        completed_at=completed_at,
                        updated_at=completed_at,
                    )
                )

                database_result = await session.execute(statement)

        # A zero row count means the job was no longer owned by this worker.
        return database_result.rowcount == 1

    async def mark_failed(
        self,
        *,
        job_id: uuid.UUID,
        worker_id: str,
        error_message: str,
    ) -> bool:
        """Record a terminal failure for the currently owned job."""

        completed_at = datetime.now(UTC)

        async with self._session_factory() as session:
            async with session.begin():
                statement = (
                    update(Job)
                    .where(
                        Job.id == job_id,
                        Job.status == JobStatus.RUNNING,
                        Job.worker_id == worker_id,
                    )
                    .values(
                        # Phase 4 will replace this immediate terminal state
                        # with retry scheduling and exponential backoff.
                        status=JobStatus.DEAD_LETTERED,
                        result=None,
                        last_error=error_message[:4000],
                        completed_at=completed_at,
                        updated_at=completed_at,
                    )
                )

                database_result = await session.execute(statement)

        return database_result.rowcount == 1
