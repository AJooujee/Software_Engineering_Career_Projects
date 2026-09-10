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


@lru_cache
def get_settings() -> Settings:
    return Settings()
