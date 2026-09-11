"""Tests for worker success and failure processing paths."""

from typing import Any
from uuid import UUID, uuid4

from job_system.worker import JobWorker


class FakeJobQueue:
    """Record worker state transitions without using PostgreSQL."""

    def __init__(self) -> None:
        self.succeeded_jobs: list[dict[str, Any]] = []
        self.failed_jobs: list[dict[str, Any]] = []

    async def mark_succeeded(
        self,
        *,
        job_id: UUID,
        worker_id: str,
        result_payload: dict[str, Any],
    ) -> bool:
        """Record a successful job transition."""

        self.succeeded_jobs.append(
            {
                "job_id": job_id,
                "worker_id": worker_id,
                "result_payload": result_payload,
            }
        )
        return True

    async def mark_failed(
        self,
        *,
        job_id: UUID,
        worker_id: str,
        error_message: str,
    ) -> bool:
        """Record a failed job transition."""

        self.failed_jobs.append(
            {
                "job_id": job_id,
                "worker_id": worker_id,
                "error_message": error_message,
            }
        )
        return True


class FakeJob:
    """Provide only the job attributes required by JobWorker."""

    def __init__(
        self,
        *,
        task_name: str,
        payload: dict[str, Any],
    ) -> None:
        self.id = uuid4()
        self.task_name = task_name
        self.payload = payload


def create_worker(queue: FakeJobQueue) -> JobWorker:
    """Create a single-slot worker for isolated unit tests."""

    return JobWorker(
        queue,  # type: ignore[arg-type]
        worker_id="test-worker",
        queue_names=("default",),
        concurrency=1,
        poll_interval_seconds=0.01,
    )


async def test_worker_marks_successful_job() -> None:
    queue = FakeJobQueue()
    worker = create_worker(queue)
    job = FakeJob(
        task_name="generate-report",
        payload={
            "report_id": "test-report",
            "format": "json",
            "delay_seconds": 0,
        },
    )

    # Directly test one processing cycle without starting an infinite poll loop.
    await worker._process_job(job, slot_number=1)  # type: ignore[arg-type]

    assert queue.failed_jobs == []
    assert queue.succeeded_jobs == [
        {
            "job_id": job.id,
            "worker_id": "test-worker",
            "result_payload": {
                "report_id": "test-report",
                "format": "json",
                "generated": True,
            },
        }
    ]


async def test_worker_marks_failed_job() -> None:
    queue = FakeJobQueue()
    worker = create_worker(queue)
    job = FakeJob(
        task_name="send-email",
        payload={
            "subject": "Missing recipient",
            "delay_seconds": 0,
        },
    )

    # Invalid task input must become a persisted terminal failure.
    await worker._process_job(job, slot_number=1)  # type: ignore[arg-type]

    assert queue.succeeded_jobs == []
    assert len(queue.failed_jobs) == 1
    assert queue.failed_jobs[0]["job_id"] == job.id
    assert queue.failed_jobs[0]["worker_id"] == "test-worker"
    assert queue.failed_jobs[0]["error_message"] == (
        "InvalidTaskPayloadError: recipient must be a non-empty string"
    )
