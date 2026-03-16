from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = 'Meeting Room Reservation System'
    api_v1_prefix: str = '/api/v1'
    debug: bool = False

    database_url: str = 'postgresql+psycopg://postgres:postgres@localhost:5432/meeting_room'
    redis_url: str = 'redis://localhost:6379/0'

    jwt_secret_key: str = 'CHANGE_ME_TO_A_LONG_RANDOM_SECRET'
    jwt_algorithm: str = 'HS256'
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    booking_lock_ttl_seconds: int = 10
    room_cache_ttl_seconds: int = 300
    room_schedule_cache_ttl_seconds: int = 60

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
