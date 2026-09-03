"""Environment-based configuration for the Cloud Operations API."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# Locate the project root independently of the current terminal directory.
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Define application settings loaded from environment variables."""

    app_env: str = "development"
    database_url: str

    # Load the private .env file while ignoring unrelated frontend variables.
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return one cached settings instance for the application process."""

    return Settings()