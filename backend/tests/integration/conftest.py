from __future__ import annotations

import os

import pytest

from app.db.session import engine


@pytest.fixture(autouse=True)
def require_mysql_integration_environment() -> None:
    if not os.environ.get('MYSQL_TEST_DATABASE_URL'):
        pytest.skip('Set MYSQL_TEST_DATABASE_URL and REDIS_TEST_URL to run integration tests.')
    assert engine.dialect.name == 'mysql'
