"""Tests for worker success and failure processing paths."""

import asyncio
from typing import Any
from uuid import UUID, uuid4

import pytest

from job_system.models import JobStatus
from job_system.worker import JobWorker


class FakeJobQueue:
    """Record worker state transitions without using PostgreSQL."""

    def __init__(self) -> None:
        self.succeeded_jobs: list[dict[str, Any]] = []
        self.failed_jobs: list[dict[str, Any]] = []
        self.renewed_jobs: list[dict[str, Any]] = []
        self.recovery_limits: list[int] = []
        self.lease_renewed = asyncio.Event()
        self.recovery_completed = asyncio.Event()

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
        retryable: bool,
        retry_base_delay_seconds: float,
        retry_max_delay_seconds: float,
    ) -> JobStatus:
        """Record a failed job transition."""

        self.failed_jobs.append(
            {
                "job_id": job_id,
                "worker_id": worker_id,
                "error_message": error_message,
                "retryable": retryable,
                "retry_base_delay_seconds": retry_base_delay_seconds,
                "retry_max_delay_seconds": retry_max_delay_seconds,
            }
        )
        return JobStatus.DEAD_LETTERED

    async def renew_lease(
        self,
        *,
        job_id: UUID,
        worker_id: str,
        lease_duration_seconds: float,
    ) -> bool:
        """Record one heartbeat lease renewal."""

        self.renewed_jobs.append(
            {
                "job_id": job_id,
                "worker_id": worker_id,
                "lease_duration_seconds": lease_duration_seconds,
            }
        )
        self.lease_renewed.set()
        return True

    async def recover_stale_jobs(
        self,
        *,
        limit: int,
    ) -> tuple[int, int]:
        """Record one stale-job recovery scan."""

        self.recovery_limits.append(limit)
        self.recovery_completed.set()
        return 1, 1


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
        retry_base_delay_seconds=5.0,
        retry_max_delay_seconds=300.0,
        lease_duration_seconds=30.0,
        heartbeat_interval_seconds=5.0,
        recovery_interval_seconds=10.0,
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
    assert queue.failed_jobs[0]["retryable"] is False
    assert queue.failed_jobs[0]["retry_base_delay_seconds"] == 5.0
    assert queue.failed_jobs[0]["retry_max_delay_seconds"] == 300.0


async def test_worker_marks_temporary_error_as_retryable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    queue = FakeJobQueue()
    worker = create_worker(queue)
    job = FakeJob(
        task_name="temporary-task",
        payload={},
    )

    async def raise_temporary_error(
        task_name: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        del task_name, payload
        raise RuntimeError("temporary service unavailable")

    monkeypatch.setattr(
        "job_system.worker.execute_task",
        raise_temporary_error,
    )

    await worker._process_job(job, slot_number=1)  # type: ignore[arg-type]

    assert queue.succeeded_jobs == []
    assert len(queue.failed_jobs) == 1
    assert queue.failed_jobs[0]["error_message"] == ("RuntimeError: temporary service unavailable")
    assert queue.failed_jobs[0]["retryable"] is True
    assert queue.failed_jobs[0]["retry_base_delay_seconds"] == 5.0
    assert queue.failed_jobs[0]["retry_max_delay_seconds"] == 300.0


async def test_worker_renews_active_job_lease() -> None:
    queue = FakeJobQueue()
    worker = create_worker(queue)
    worker.heartbeat_interval_seconds = 0.001
    job_id = uuid4()
    stop_event = asyncio.Event()

    heartbeat_task = asyncio.create_task(worker._maintain_lease(job_id, stop_event))

    await asyncio.wait_for(
        queue.lease_renewed.wait(),
        timeout=1,
    )
    stop_event.set()
    await heartbeat_task

    assert queue.renewed_jobs == [
        {
            "job_id": job_id,
            "worker_id": "test-worker",
            "lease_duration_seconds": 30.0,
        }
    ]


async def test_worker_runs_stale_job_recovery() -> None:
    queue = FakeJobQueue()
    worker = create_worker(queue)

    recovery_task = asyncio.create_task(worker._run_recovery_loop())

    await asyncio.wait_for(
        queue.recovery_completed.wait(),
        timeout=1,
    )
    worker.request_stop()
    await recovery_task

    assert queue.recovery_limits == [100]
