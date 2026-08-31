from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
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
    """Runtime configuration for the Order Service."""

    database_url: str = Field(
        validation_alias=AliasChoices(
            "ORDER_DATABASE_URL",
            "DATABASE_URL",
        )
    )
    inventory_service_url: str = Field(
        default="http://127.0.0.1:8001",
        validation_alias=AliasChoices(
            "ORDER_INVENTORY_SERVICE_URL",
            "INVENTORY_SERVICE_URL",
        ),
    )
    warehouse_service_url: str = Field(
        default="http://127.0.0.1:8002",
        validation_alias=AliasChoices(
            "ORDER_WAREHOUSE_SERVICE_URL",
            "WAREHOUSE_SERVICE_URL",
        ),
    )
    service_request_timeout_seconds: float = Field(
        default=5.0,
        gt=0,
        le=30,
        validation_alias=AliasChoices(
            "ORDER_SERVICE_REQUEST_TIMEOUT_SECONDS",
            "SERVICE_REQUEST_TIMEOUT_SECONDS",
        ),
    )

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator(
        "inventory_service_url",
        "warehouse_service_url",
    )
    @classmethod
    def remove_trailing_slash(cls, value: str) -> str:
        """Keep endpoint construction consistent across environments."""

        return value.rstrip("/")


@lru_cache
def get_settings() -> Settings:
    """Load and cache application settings."""

    return Settings()