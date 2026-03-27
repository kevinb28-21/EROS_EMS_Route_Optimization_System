"""
Application configuration using Pydantic Settings.
Loads values from environment variables with sensible defaults.
"""

import os

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database (defaults to SQLite for easy local dev; use PostgreSQL on Railway / Docker)
    database_url: str = "sqlite:///./eros.db"

    # API (Railway and similar platforms inject PORT; local dev uses api_port)
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True

    # CORS
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Simulation
    simulation_enabled: bool = True
    simulation_interval_seconds: int = 5

    # Optional OSRM URL for external routing
    osrm_url: str | None = None

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def listen_port(self) -> int:
        """Listen port: Railway/cloud set PORT; otherwise api_port (e.g. 8000)."""
        return int(os.environ.get("PORT", str(self.api_port)))


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
