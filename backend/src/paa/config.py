"""Runtime configuration, read from environment variables prefixed ``PAA_``.

A ``.env`` file in the working directory is honoured for local development.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PAA_", env_file=".env", extra="ignore")

    database_url: str = "postgresql://paa:paa@localhost:5432/paa"
    """psycopg connection string. Never exposed to the browser."""

    data_dir: Path = Path("../data")
    """Where downloaded source files live. Large; git-ignored."""

    postcode_areas: str = ""
    """Comma-separated postcode areas (e.g. ``EN,N``) to restrict loads to while prototyping.
    Empty means load everything."""

    cors_origins: str = "http://localhost:5173"
    """Comma-separated origins allowed to call the API from a browser."""

    http_timeout_s: float = Field(default=120.0, gt=0)
    """Timeout for source downloads."""

    listing_webhook_url: str = ""
    """The stage-0 analysis engine: an n8n webhook that takes ``{"url": ...}`` and returns the
    investment analysis. Empty disables ``POST /api/listings/analyse``."""

    listing_timeout_s: float = Field(default=240.0, gt=0)
    """How long to wait for the listing engine; it runs an LLM and takes a minute or more."""

    listing_cache_hours: float = Field(default=24.0, ge=0)
    """Re-use a stored analysis of the same URL younger than this instead of calling the engine."""

    @property
    def postcode_area_list(self) -> list[str]:
        return [a.strip().upper() for a in self.postcode_areas.split(",") if a.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
