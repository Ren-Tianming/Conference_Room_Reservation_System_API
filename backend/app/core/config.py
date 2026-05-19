from __future__ import annotations

from typing import Optional

from pydantic import Field, model_validator
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
    bootstrap_admin_username: Optional[str] = None
    bootstrap_admin_password: Optional[str] = None

    database_url: str = "mysql+pymysql://conference_user:conference_password@127.0.0.1:3306/conference_room?charset=utf8mb4"
    redis_url: str = "redis://localhost:6379/0"
    auto_create_tables: bool = True

    cors_origins: list[str] = Field(default_factory=lambda: [
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ])
    require_redis_for_locks: bool = False
    require_redis_for_token_blacklist: bool = False

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.env.lower() in {"prod", "production"}:
            if self.debug:
                raise ValueError("DEBUG must be false in production.")
            if self.secret_key == "change-this-to-a-strong-secret":
                raise ValueError("SECRET_KEY must be changed in production.")
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
