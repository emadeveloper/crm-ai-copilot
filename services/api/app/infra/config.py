"""Application settings, loaded from the environment (12-factor)."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Persistence
    database_url: str = Field(description="Async SQLAlchemy URL (postgresql+asyncpg://...)")

    # LLM provider (Gemini AI Studio free tier)
    gemini_api_key: str = Field(description="Google AI Studio API key")
    llm_model: str = Field(default="gemini-2.5-flash", description="Flash-class model id")
    llm_rate_per_min: int = Field(
        default=15, ge=1, description="Client-side request budget per minute"
    )

    # CRM gateway (HubSpot Private App)
    hubspot_private_app_token: str = Field(description="HubSpot Private App access token")

    # Pipeline worker
    max_task_attempts: int = Field(default=5, ge=1)
    worker_poll_interval_seconds: float = Field(default=2.0, gt=0)

    # Observability
    log_level: str = Field(default="INFO")


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings singleton (values are read from the environment)."""
    return Settings()
