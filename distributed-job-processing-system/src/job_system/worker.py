"""Asynchronous worker runtime for processing queued jobs."""

import asyncio
import logging
import os
import socket
from uuid import uuid4

from job_system.config import get_settings
from job_system.db import SessionFactory
from job_system.handlers import execute_task
from job_system.models import Job
from job_system.queue import PostgresJobQueue

logger = logging.getLogger(__name__)


class JobWorker:
    """Claim and process jobs concurrently from PostgreSQL."""

    def __init__(
        self,
        queue: PostgresJobQueue,
        *,
        worker_id: str,
        queue_names: tuple[str, ...],
        concurrency: int,
        poll_interval_seconds: float,
    ) -> None:
        self.queue = queue
        self.worker_id = worker_id
        self.queue_names = queue_names
        self.concurrency = concurrency
        self.poll_interval_seconds = poll_interval_seconds
        self._stop_event = asyncio.Event()

    def request_stop(self) -> None:
        """Ask all worker slots to stop after their current jobs finish."""

        logger.info("Worker shutdown requested")
        self._stop_event.set()

    async def run(self) -> None:
        """Run concurrent worker slots until shutdown is requested."""

        logger.info(
            "Starting worker %s with %s slots for queues %s",
            self.worker_id,
            self.concurrency,
            ", ".join(self.queue_names),
        )

        # Each slot independently claims and processes one job at a time.
        async with asyncio.TaskGroup() as task_group:
            for slot_number in range(1, self.concurrency + 1):
                task_group.create_task(
                    self._run_slot(slot_number),
                    name=f"worker-slot-{slot_number}",
                )

        logger.info("Worker %s stopped", self.worker_id)

    async def _run_slot(self, slot_number: int) -> None:
        """Continuously claim and execute jobs for one concurrency slot."""

        logger.info("Worker slot %s started", slot_number)

        while not self._stop_event.is_set():
            try:
                jobs = await self.queue.claim_jobs(
                    worker_id=self.worker_id,
                    queues=self.queue_names,
                    limit=1,
                )
            except Exception:
                # A temporary database error must not terminate the whole worker.
                logger.exception("Worker slot %s could not claim a job", slot_number)
                await self._wait_before_polling()
                continue

            if not jobs:
                await self._wait_before_polling()
                continue

            await self._process_job(jobs[0], slot_number)

        logger.info("Worker slot %s stopped", slot_number)

    async def _process_job(self, job: Job, slot_number: int) -> None:
        """Execute one claimed job and persist its final state."""

        logger.info(
            "Worker slot %s processing job %s (%s)",
            slot_number,
            job.id,
            job.task_name,
        )

        try:
            result = await execute_task(job.task_name, job.payload)

            updated = await self.queue.mark_succeeded(
                job_id=job.id,
                worker_id=self.worker_id,
                result_payload=result,
            )

            if updated:
                logger.info("Job %s succeeded", job.id)
            else:
                logger.warning(
                    "Job %s could not be marked succeeded because ownership changed",
                    job.id,
                )
        except asyncio.CancelledError:
            # Cancellation must remain cancellation instead of becoming job failure.
            raise
        except Exception as exc:
            logger.exception("Job %s failed", job.id)

            try:
                updated = await self.queue.mark_failed(
                    job_id=job.id,
                    worker_id=self.worker_id,
                    error_message=f"{type(exc).__name__}: {exc}",
                )

                if not updated:
                    logger.warning(
                        "Job %s could not be marked failed because ownership changed",
                        job.id,
                    )
            except Exception:
                # Persistence errors are isolated to this job so that the other
                # worker slots can continue processing available jobs.
                logger.exception(
                    "Worker could not persist the failure state for job %s",
                    job.id,
                )

    async def _wait_before_polling(self) -> None:
        """Wait for new work while allowing prompt graceful shutdown."""

        try:
            await asyncio.wait_for(
                self._stop_event.wait(),
                timeout=self.poll_interval_seconds,
            )
        except TimeoutError:
            # A timeout simply means that the slot should poll again.
            pass


def create_worker_id() -> str:
    """Create an identifier that distinguishes this worker process."""

    hostname = socket.gethostname()
    process_id = os.getpid()
    unique_suffix = uuid4().hex[:8]
    return f"{hostname}-{process_id}-{unique_suffix}"


async def run_worker() -> None:
    """Configure and run one worker process."""

    settings = get_settings()
    queue = PostgresJobQueue(SessionFactory)

    worker = JobWorker(
        queue,
        worker_id=create_worker_id(),
        queue_names=settings.worker_queue_names,
        concurrency=settings.worker_concurrency,
        poll_interval_seconds=settings.worker_poll_interval_seconds,
    )

    worker_task = asyncio.create_task(worker.run())

    try:
        # Shield prevents Ctrl+C from immediately cancelling active job handlers.
        await asyncio.shield(worker_task)
    except asyncio.CancelledError:
        # Stop claiming new jobs, but allow currently running jobs to finish.
        worker.request_stop()
        await worker_task


def main() -> None:
    """Start the worker from the command line."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Worker interrupted")


if __name__ == "__main__":
    main()
