from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Conference Room Reservation System API"
    env: str = "dev"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    secret_key: str = "change-this-to-a-strong-secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    database_url: str = "sqlite:///./conference_room.db"
    redis_url: str = "redis://localhost:6379/0"
    auto_create_tables: bool = True

    cors_origins: list[str] = Field(default_factory=lambda: [
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ])

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
