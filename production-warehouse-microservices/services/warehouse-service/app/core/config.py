from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def find_env_file() -> Path | None:
    """Find the nearest project .env file when running outside Docker."""
    current_file = Path(__file__).resolve()

    for parent_directory in current_file.parents:
        candidate = parent_directory / ".env"

        if candidate.is_file():
            return candidate

    # Docker receives settings through container environment variables,
    # so an .env file is optional inside the image.
    return None


ENV_FILE = find_env_file()


class Settings(BaseSettings):
    """Environment-backed configuration for the Warehouse Service."""

    database_url: str

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        env_prefix="WAREHOUSE_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Load settings once and reuse them throughout the application."""
    return Settings()