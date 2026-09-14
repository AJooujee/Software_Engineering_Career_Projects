from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Observability & Incident Detection Platform"
    app_version: str = "0.1.0"
    environment: Literal["development", "testing", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="OBSERVABILITY_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
