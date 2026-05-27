from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.engine import make_url

BACKEND_ROOT = Path(__file__).resolve().parents[1]
TEST_DB = Path(__file__).parent / 'test_conference_room.db'
MYSQL_TEST_DATABASE_URL = os.environ.get('MYSQL_TEST_DATABASE_URL')
USING_MYSQL_INTEGRATION = MYSQL_TEST_DATABASE_URL is not None

os.environ['ENV'] = 'test'
os.environ['DEBUG'] = 'false'
os.environ['LOG_LEVEL'] = 'INFO'

if USING_MYSQL_INTEGRATION:
    test_database_url = make_url(MYSQL_TEST_DATABASE_URL)
    database_name = test_database_url.database or ''
    if test_database_url.get_backend_name() != 'mysql':
        raise RuntimeError('MYSQL_TEST_DATABASE_URL must use a MySQL dialect.')
    if 'test' not in database_name.lower():
        raise RuntimeError("MYSQL_TEST_DATABASE_URL database name must contain 'test'; integration tests reset its schema.")
    os.environ['DATABASE_URL'] = MYSQL_TEST_DATABASE_URL
    os.environ['REDIS_URL'] = os.environ.get('REDIS_TEST_URL', 'redis://127.0.0.1:6380/15')
    os.environ['REQUIRE_REDIS_FOR_LOCKS'] = 'true'
    os.environ['REQUIRE_REDIS_FOR_TOKEN_BLACKLIST'] = 'true'
else:
    os.environ['DATABASE_URL'] = f'sqlite:///{TEST_DB}'
    os.environ['REDIS_URL'] = 'redis://127.0.0.1:0/0'

os.environ['AUTO_CREATE_TABLES'] = 'false'
os.environ['SECRET_KEY'] = 'test-secret-key-with-at-least-32-characters'

from app.core import redis_client  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402


def run_migrations(revision: str = 'head') -> None:
    alembic_cfg = Config(str(BACKEND_ROOT / 'alembic.ini'))
    alembic_cfg.set_main_option('script_location', str(BACKEND_ROOT / 'alembic'))
    alembic_cfg.set_main_option('sqlalchemy.url', os.environ['DATABASE_URL'])
    if revision == 'base':
        command.downgrade(alembic_cfg, revision)
    else:
        command.upgrade(alembic_cfg, revision)


def reset_database() -> None:
    engine.dispose()
    if USING_MYSQL_INTEGRATION:
        run_migrations('base')
    else:
        TEST_DB.unlink(missing_ok=True)
    run_migrations()


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    reset_database()
    if USING_MYSQL_INTEGRATION:
        redis_client._cached_client = redis_client._SENTINEL
        client = redis_client.get_redis_client()
        if client is None:
            pytest.fail('Redis test instance is required for MySQL integration tests.')
        client.flushdb()
    with TestClient(app) as test_client:
        yield test_client
    engine.dispose()
    if not USING_MYSQL_INTEGRATION:
        TEST_DB.unlink(missing_ok=True)
