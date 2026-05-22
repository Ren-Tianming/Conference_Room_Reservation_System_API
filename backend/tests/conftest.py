from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
TEST_DB = Path(__file__).parent / 'test_conference_room.db'
os.environ['DATABASE_URL'] = f'sqlite:///{TEST_DB}'
os.environ['AUTO_CREATE_TABLES'] = 'false'
os.environ['REDIS_URL'] = 'redis://127.0.0.1:0/0'
os.environ['SECRET_KEY'] = 'test-secret-key'

from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402


def run_migrations() -> None:
    alembic_cfg = Config(str(BACKEND_ROOT / 'alembic.ini'))
    alembic_cfg.set_main_option('script_location', str(BACKEND_ROOT / 'alembic'))
    alembic_cfg.set_main_option('sqlalchemy.url', os.environ['DATABASE_URL'])
    command.upgrade(alembic_cfg, 'head')


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    engine.dispose()
    TEST_DB.unlink(missing_ok=True)
    run_migrations()
    with TestClient(app) as test_client:
        yield test_client
    engine.dispose()
    TEST_DB.unlink(missing_ok=True)
