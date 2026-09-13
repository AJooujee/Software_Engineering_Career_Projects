from functools import lru_cache
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="JOB_",
        extra="ignore",
        case_sensitive=False,
    )

    database_url: str = "postgresql+asyncpg://job_user:local_dev_password@localhost:5433/job_system"
    database_echo: bool = False
    database_pool_size: int = Field(default=5, ge=1, le=50)
    database_max_overflow: int = Field(default=10, ge=0, le=100)
    # Queues that each worker instance is allowed to consume.
    worker_queues: str = "default,reports,emails"

    # Number of jobs that one worker process may execute concurrently.
    worker_concurrency: int = Field(default=4, ge=1, le=64)

    # Delay before polling PostgreSQL again when no job is available.
    worker_poll_interval_seconds: float = Field(default=0.5, gt=0, le=30)

    # Initial delay before the first retry attempt.
    worker_retry_base_delay_seconds: float = Field(
        default=5.0,
        ge=0,
        le=3600,
    )

    # Upper bound prevents exponential backoff from growing indefinitely.
    worker_retry_max_delay_seconds: float = Field(
        default=300.0,
        ge=0,
        le=86400,
    )

    # Duration of worker ownership before a missing heartbeat makes it stale.
    worker_lease_duration_seconds: float = Field(
        default=30.0,
        gt=0,
        le=3600,
    )

    # Frequency used to renew leases for actively running jobs.
    worker_heartbeat_interval_seconds: float = Field(
        default=5.0,
        gt=0,
        le=300,
    )

    # Frequency used to scan for jobs abandoned by crashed workers.
    worker_recovery_interval_seconds: float = Field(
        default=10.0,
        gt=0,
        le=300,
    )

    @model_validator(mode="after")
    def validate_worker_lease_intervals(self) -> Self:
        """Ensure active workers renew their leases before expiration."""

        if self.worker_heartbeat_interval_seconds >= self.worker_lease_duration_seconds:
            raise ValueError("worker heartbeat interval must be shorter than worker lease duration")

        return self

    @property
    def worker_queue_names(self) -> tuple[str, ...]:
        """Return normalized queue names configured for the worker."""

        queue_names = tuple(
            queue_name.strip() for queue_name in self.worker_queues.split(",") if queue_name.strip()
        )

        # Always provide a valid fallback if the environment value is empty.
        return queue_names or ("default",)


@lru_cache
def get_settings() -> Settings:
    return Settings()
