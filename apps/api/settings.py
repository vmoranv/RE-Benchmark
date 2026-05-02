"""Pydantic-Settings configuration for the API."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="JSREBENCH_", env_file=".env", extra="ignore")

    database_url: str = Field(
        default="postgresql+psycopg://bench:bench@localhost:5432/jsrebench",
        description="Async SQLAlchemy URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0")
    artifact_root: str = Field(default="./artifacts")
    sandbox_profiles_dir: str = Field(default="./infra/sandbox/profiles")

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_allow_origins: list[str] = Field(default_factory=lambda: ["*"])

    anthropic_api_key: str | None = None
    anthropic_default_model: str = "claude-opus-4-7-20260101"

    log_level: str = "INFO"


settings = Settings()
