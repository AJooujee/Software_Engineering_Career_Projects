import uuid
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from httpx2 import AsyncClient

from job_system.api.jobs import get_job_service
from job_system.main import app
from job_system.models import Job, JobStatus
from job_system.schemas import JobCreate


class FakeJobService:
    """In-memory service used to test HTTP behavior without touching PostgreSQL."""

    def __init__(self) -> None:
        self.jobs: dict[uuid.UUID, Job] = {}

    async def create_job(self, job_data: JobCreate) -> Job:
        now = datetime.now(UTC)

        job = Job(
            id=uuid.uuid4(),
            queue=job_data.queue,
            task_name=job_data.task_name,
            payload=job_data.payload,
            status=JobStatus.QUEUED,
            priority=job_data.priority,
            created_at=now,
            updated_at=now,
        )

        self.jobs[job.id] = job
        return job

    async def get_job(self, job_id: uuid.UUID) -> Job | None:
        return self.jobs.get(job_id)

    async def get_jobs(
        self,
        *,
        queue: str | None = None,
        status: JobStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Job]:
        jobs = list(self.jobs.values())

        if queue is not None:
            jobs = [job for job in jobs if job.queue == queue]

        if status is not None:
            jobs = [job for job in jobs if job.status == status]

        jobs.sort(
            key=lambda job: (job.created_at, str(job.id)),
            reverse=True,
        )

        return jobs[offset : offset + limit]


@pytest.fixture
def fake_job_service() -> Iterator[FakeJobService]:
    """Replace the database service for each API test."""

    service = FakeJobService()

    async def override_job_service() -> FakeJobService:
        return service

    app.dependency_overrides[get_job_service] = override_job_service

    yield service

    # Prevent one test's dependency override from leaking into another test.
    app.dependency_overrides.pop(get_job_service, None)


async def test_create_and_fetch_job(
    client: AsyncClient,
    fake_job_service: FakeJobService,
) -> None:
    create_response = await client.post(
        "/jobs",
        json={
            "queue": "reports",
            "task_name": "generate-report",
            "payload": {"format": "pdf"},
            "priority": 10,
        },
    )

    assert create_response.status_code == 201
    created_job = create_response.json()
    assert created_job["status"] == "queued"

    fetch_response = await client.get(f"/jobs/{created_job['id']}")

    assert fetch_response.status_code == 200
    assert fetch_response.json() == created_job


async def test_list_jobs_with_filters(
    client: AsyncClient,
    fake_job_service: FakeJobService,
) -> None:
    await client.post(
        "/jobs",
        json={
            "queue": "reports",
            "task_name": "generate-report",
        },
    )
    await client.post(
        "/jobs",
        json={
            "queue": "emails",
            "task_name": "send-email",
        },
    )

    response = await client.get(
        "/jobs",
        params={
            "queue": "reports",
            "status": "queued",
        },
    )

    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 1
    assert jobs[0]["queue"] == "reports"


async def test_get_unknown_job_returns_404(
    client: AsyncClient,
    fake_job_service: FakeJobService,
) -> None:
    response = await client.get(f"/jobs/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Job not found"}


async def test_create_job_rejects_invalid_priority(
    client: AsyncClient,
    fake_job_service: FakeJobService,
) -> None:
    response = await client.post(
        "/jobs",
        json={
            "task_name": "generate-report",
            "priority": 101,
        },
    )

    assert response.status_code == 422
