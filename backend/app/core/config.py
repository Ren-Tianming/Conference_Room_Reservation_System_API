from __future__ import annotations

import json
import secrets
from typing import Optional

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    app_name: str = "Conference Room Reservation System API"
    env: str = "dev"
    debug: bool = True
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    secret_key: str = "change-this-to-a-strong-secret"
    algorithm: str = "HS256"
    jwt_issuer: str = "conference-room-api"
    jwt_audience: str = "conference-room-users"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    bootstrap_admin_username: Optional[str] = None
    bootstrap_admin_password: Optional[str] = None
    auth_rate_limit_max_attempts: int = 5
    auth_rate_limit_window_seconds: int = 60

    database_url: Optional[str] = None
    database_driver: str = "mysql+pymysql"
    database_host: str = "127.0.0.1"
    database_port: int = 3306
    database_name: str = "conference_room"
    database_user: str = "conference_user"
    database_password: str = "conference_password"
    database_query: str = "charset=utf8mb4"
    redis_url: str = "redis://localhost:6379/0"
    auto_create_tables: bool = True

    cors_origins: str = "http://localhost:8501,http://127.0.0.1:8501"
    require_redis_for_locks: bool = False
    require_redis_for_token_blacklist: bool = False

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, value: str) -> str:
        origins = cls.parse_cors_origins(value)
        if not origins:
            raise ValueError("CORS_ORIGINS must contain at least one origin.")
        return value

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        normalized = value.upper()
        if normalized not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of: {', '.join(sorted(allowed))}.")
        return normalized

    @field_validator("algorithm")
    @classmethod
    def validate_algorithm(cls, value: str) -> str:
        allowed = {"HS256", "HS384", "HS512"}
        normalized = value.upper()
        if normalized not in allowed:
            raise ValueError(f"ALGORITHM must be one of: {', '.join(sorted(allowed))}.")
        return normalized

    @field_validator("access_token_expire_minutes", "refresh_token_expire_days")
    @classmethod
    def validate_positive_expiry(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Token expiration values must be positive.")
        return value

    @field_validator("auth_rate_limit_max_attempts", "auth_rate_limit_window_seconds")
    @classmethod
    def validate_positive_auth_limit(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Auth rate limit settings must be positive.")
        return value

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.env.lower() in {"prod", "production"}:
            if self.debug:
                raise ValueError("DEBUG must be false in production.")
            if self.secret_key == "change-this-to-a-strong-secret":
                raise ValueError("SECRET_KEY must be changed in production.")
            if len(self.secret_key) < 32:
                raise ValueError("SECRET_KEY must be at least 32 characters in production.")
            if not self.jwt_issuer.strip():
                raise ValueError("JWT_ISSUER must be set in production.")
            if not self.jwt_audience.strip():
                raise ValueError("JWT_AUDIENCE must be set in production.")
            if "*" in self.cors_origin_list:
                raise ValueError("CORS_ORIGINS must not contain '*' in production.")
            if self.auto_create_tables:
                raise ValueError("AUTO_CREATE_TABLES must be false in production.")
            if not self.require_redis_for_locks:
                raise ValueError("REQUIRE_REDIS_FOR_LOCKS must be true in production.")
            if not self.require_redis_for_token_blacklist:
                raise ValueError("REQUIRE_REDIS_FOR_TOKEN_BLACKLIST must be true in production.")
        return self

    @property
    def is_production(self) -> bool:
        return self.env.lower() in {"prod", "production"}

    @property
    def cors_origin_list(self) -> list[str]:
        return self.parse_cors_origins(self.cors_origins)

    @property
    def sqlalchemy_database_url(self) -> str | URL:
        if self.database_url:
            return self.database_url
        query = self.parse_database_query(self.database_query)
        return URL.create(
            drivername=self.database_driver,
            username=self.database_user,
            password=self.database_password,
            host=self.database_host,
            port=self.database_port,
            database=self.database_name,
            query=query,
        )

    @property
    def sqlalchemy_database_url_string(self) -> str:
        url = self.sqlalchemy_database_url
        if isinstance(url, URL):
            return url.render_as_string(hide_password=False)
        return url

    @staticmethod
    def generate_secret_key() -> str:
        return secrets.token_urlsafe(48)

    @staticmethod
    def parse_database_query(value: str) -> dict[str, str]:
        if not value.strip():
            return {}
        return dict(item.split("=", 1) for item in value.split("&") if "=" in item)

    @staticmethod
    def parse_cors_origins(value: str) -> list[str]:
        value = value.strip()
        if not value:
            return []
        if value.startswith("["):
            parsed = json.loads(value)
            if not isinstance(parsed, list):
                raise ValueError("CORS_ORIGINS JSON value must be a list.")
            return [str(origin).strip() for origin in parsed if str(origin).strip()]
        return [origin.strip() for origin in value.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
