from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_DB = Path(__file__).parent / 'test_conference_room.db'
os.environ['DATABASE_URL'] = f'sqlite:///{TEST_DB}'
os.environ['AUTO_CREATE_TABLES'] = 'true'
os.environ['REDIS_URL'] = 'redis://127.0.0.1:0/0'
os.environ['SECRET_KEY'] = 'test-secret-key'

from app.db.base import Base  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)
