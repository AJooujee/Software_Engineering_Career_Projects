from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def find_env_file() -> Path | None:
    """Find the shared project .env file without assuming a fixed path depth."""

    for parent_directory in Path(__file__).resolve().parents:
        candidate = parent_directory / ".env"

        if candidate.is_file():
            return candidate

    # Docker Compose injects environment variables directly, so the file
    # does not need to exist inside the container.
    return None


ENV_FILE = find_env_file()


class Settings(BaseSettings):
    """Runtime configuration for the API Gateway."""

    service_name: str = "api-gateway"

    inventory_service_url: str = Field(
        default="http://127.0.0.1:8001",
        validation_alias=AliasChoices(
            "GATEWAY_INVENTORY_SERVICE_URL",
            "INVENTORY_SERVICE_URL",
        ),
    )

    warehouse_service_url: str = Field(
        default="http://127.0.0.1:8002",
        validation_alias=AliasChoices(
            "GATEWAY_WAREHOUSE_SERVICE_URL",
            "WAREHOUSE_SERVICE_URL",
        ),
    )

    order_service_url: str = Field(
        default="http://127.0.0.1:8003",
        validation_alias=AliasChoices(
            "GATEWAY_ORDER_SERVICE_URL",
            "ORDER_SERVICE_URL",
        ),
    )

    service_request_timeout_seconds: float = Field(
        default=5.0,
        gt=0,
        validation_alias=AliasChoices(
            "GATEWAY_SERVICE_REQUEST_TIMEOUT_SECONDS",
            "SERVICE_REQUEST_TIMEOUT_SECONDS",
        ),
    )

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return one cached settings instance for the process."""

    return Settings()