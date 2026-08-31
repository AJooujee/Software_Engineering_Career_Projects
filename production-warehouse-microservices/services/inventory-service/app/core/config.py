from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

def find_env_file() -> Path | None:
    """Find the shared local .env file without assuming a fixed path depth."""

    for parent_directory in Path(__file__).resolve().parents:
        candidate = parent_directory / ".env"

        if candidate.is_file():
            return candidate

    # Docker receives configuration through environment variables,
    # so an .env file is optional inside the container.
    return None


ENV_FILE = find_env_file()

class Settings(BaseSettings):
    database_url: str

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()