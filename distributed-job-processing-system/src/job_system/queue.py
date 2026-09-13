import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from job_system.models import Job, JobStatus


def should_retry_job(
    *,
    retryable: bool,
    attempt_count: int,
    max_attempts: int,
) -> bool:
    """Return whether a failed job has another execution attempt available."""

    return retryable and attempt_count < max_attempts


def calculate_retry_delay_seconds(
    *,
    attempt_count: int,
    base_delay_seconds: float,
    max_delay_seconds: float,
) -> float:
    """Calculate capped exponential backoff for the current failed attempt."""

    exponential_delay = base_delay_seconds * (2 ** max(attempt_count - 1, 0))
    return min(exponential_delay, max_delay_seconds)


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
        lease_duration_seconds: float,
    ) -> list[Job]:
        """Atomically claim jobs that are ready for execution."""

        if not queues or limit < 1:
            return []

        claimed_at = datetime.now(UTC)
        lease_expires_at = claimed_at + timedelta(
            seconds=lease_duration_seconds,
        )

        async with self._session_factory() as session:
            async with session.begin():
                statement = (
                    select(Job)
                    .where(
                        Job.status.in_(
                            (
                                JobStatus.QUEUED,
                                JobStatus.RETRY_SCHEDULED,
                            )
                        ),
                        Job.queue.in_(queues),
                        Job.available_at <= claimed_at,
                    )
                    .order_by(
                        Job.priority.desc(),
                        Job.available_at.asc(),
                        Job.created_at.asc(),
                        Job.id.asc(),
                    )
                    # Locked rows are skipped instead of blocking other workers.
                    .with_for_update(skip_locked=True)
                    .limit(limit)
                )

                result = await session.scalars(statement)
                jobs = list(result.all())

                # The row locks remain held until all status changes are committed.
                for job in jobs:
                    job.status = JobStatus.RUNNING
                    job.worker_id = worker_id
                    job.attempt_count += 1
                    job.started_at = claimed_at
                    job.lease_expires_at = lease_expires_at
                    job.heartbeat_at = claimed_at
                    job.completed_at = None
                    job.result = None
                    job.updated_at = claimed_at

                await session.flush()

        return jobs

    async def renew_lease(
        self,
        *,
        job_id: uuid.UUID,
        worker_id: str,
        lease_duration_seconds: float,
    ) -> bool:
        """Renew an active lease only while this worker still owns the job."""

        heartbeat_at = datetime.now(UTC)
        lease_expires_at = heartbeat_at + timedelta(
            seconds=lease_duration_seconds,
        )

        async with self._session_factory() as session:
            async with session.begin():
                statement = (
                    update(Job)
                    .where(
                        Job.id == job_id,
                        Job.status == JobStatus.RUNNING,
                        Job.worker_id == worker_id,
                        Job.lease_expires_at > heartbeat_at,
                    )
                    .values(
                        heartbeat_at=heartbeat_at,
                        lease_expires_at=lease_expires_at,
                        updated_at=heartbeat_at,
                    )
                )
                database_result = await session.execute(statement)

        return database_result.rowcount == 1

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
                        Job.lease_expires_at > completed_at,
                    )
                    .values(
                        status=JobStatus.SUCCEEDED,
                        result=result_payload,
                        last_error=None,
                        completed_at=completed_at,
                        lease_expires_at=None,
                        heartbeat_at=None,
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
        retryable: bool,
        retry_base_delay_seconds: float,
        retry_max_delay_seconds: float,
    ) -> JobStatus | None:
        """Schedule a retry or dead-letter the currently owned job."""

        failed_at = datetime.now(UTC)

        async with self._session_factory() as session:
            async with session.begin():
                statement = (
                    select(Job)
                    .where(
                        Job.id == job_id,
                        Job.status == JobStatus.RUNNING,
                        Job.worker_id == worker_id,
                        Job.lease_expires_at > failed_at,
                    )
                    .with_for_update()
                )
                job = await session.scalar(statement)

                if job is None:
                    return None

                job.result = None
                job.last_error = error_message[:4000]
                job.updated_at = failed_at
                job.lease_expires_at = None
                job.heartbeat_at = None

                if should_retry_job(
                    retryable=retryable,
                    attempt_count=job.attempt_count,
                    max_attempts=job.max_attempts,
                ):
                    # Attempt one waits for base delay, attempt two waits for
                    # twice the base delay, and subsequent delays keep doubling.
                    delay_seconds = calculate_retry_delay_seconds(
                        attempt_count=job.attempt_count,
                        base_delay_seconds=retry_base_delay_seconds,
                        max_delay_seconds=retry_max_delay_seconds,
                    )

                    job.status = JobStatus.RETRY_SCHEDULED
                    job.available_at = failed_at + timedelta(
                        seconds=delay_seconds,
                    )
                    job.worker_id = None
                    job.completed_at = None
                else:
                    # Invalid tasks and jobs that exhausted all attempts are terminal.
                    job.status = JobStatus.DEAD_LETTERED
                    job.completed_at = failed_at

                await session.flush()
                return job.status

    async def recover_stale_jobs(
        self,
        *,
        limit: int,
    ) -> tuple[int, int]:
        """Recover running jobs whose worker lease has expired."""

        if limit < 1:
            return 0, 0

        recovered_at = datetime.now(UTC)
        retry_scheduled_count = 0
        dead_lettered_count = 0

        async with self._session_factory() as session:
            async with session.begin():
                statement = (
                    select(Job)
                    .where(
                        Job.status == JobStatus.RUNNING,
                        or_(
                            Job.lease_expires_at.is_(None),
                            Job.lease_expires_at <= recovered_at,
                        ),
                    )
                    .order_by(
                        Job.lease_expires_at.asc().nullsfirst(),
                        Job.id.asc(),
                    )
                    # Multiple recovery loops may run safely at the same time.
                    .with_for_update(skip_locked=True)
                    .limit(limit)
                )

                result = await session.scalars(statement)
                jobs = list(result.all())

                for job in jobs:
                    job.worker_id = None
                    job.heartbeat_at = None
                    job.lease_expires_at = None
                    job.result = None
                    job.last_error = "Worker lease expired before job completion"
                    job.updated_at = recovered_at

                    if should_retry_job(
                        retryable=True,
                        attempt_count=job.attempt_count,
                        max_attempts=job.max_attempts,
                    ):
                        # Recovery is immediately available because the failed
                        # worker no longer owns or executes this job.
                        job.status = JobStatus.RETRY_SCHEDULED
                        job.available_at = recovered_at
                        job.completed_at = None
                        retry_scheduled_count += 1
                    else:
                        job.status = JobStatus.DEAD_LETTERED
                        job.completed_at = recovered_at
                        dead_lettered_count += 1

                await session.flush()

        return retry_scheduled_count, dead_lettered_count
