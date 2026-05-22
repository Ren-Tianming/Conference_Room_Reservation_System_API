from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_database_url_builder_escapes_special_password_characters() -> None:
    settings = Settings(
        database_url=None,
        database_host='db',
        database_name='conference_room',
        database_user='conference_user',
        database_password='p@ss:w/rd#?',
        database_query='charset=utf8mb4',
    )

    url = settings.sqlalchemy_database_url_string

    assert 'p%40ss%3Aw%2Frd%23%3F' in url
    assert url.startswith('mysql+pymysql://conference_user:')
    assert url.endswith('@db:3306/conference_room?charset=utf8mb4')


def test_production_requires_redis_fail_closed_settings() -> None:
    with pytest.raises(ValidationError):
        Settings(
            env='production',
            debug=False,
            secret_key='a-production-secret-key-that-is-long-enough',
            auto_create_tables=False,
            require_redis_for_locks=False,
            require_redis_for_token_blacklist=True,
        )

    with pytest.raises(ValidationError):
        Settings(
            env='production',
            debug=False,
            secret_key='a-production-secret-key-that-is-long-enough',
            auto_create_tables=False,
            require_redis_for_locks=True,
            require_redis_for_token_blacklist=False,
        )
