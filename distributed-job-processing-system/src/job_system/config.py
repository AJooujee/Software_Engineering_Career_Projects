from functools import lru_cache

from pydantic import Field
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
