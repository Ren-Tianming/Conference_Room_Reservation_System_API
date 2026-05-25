from __future__ import annotations

import pytest
from sqlalchemy import inspect

from app.db.session import engine
from tests.conftest import run_migrations

pytestmark = pytest.mark.integration


def test_alembic_upgrade_and_downgrade_on_mysql(client) -> None:
    assert engine.dialect.name == 'mysql'
    assert {'users', 'rooms', 'bookings', 'refresh_tokens'} <= set(inspect(engine).get_table_names())

    engine.dispose()
    run_migrations('base')
    assert not ({'users', 'rooms', 'bookings', 'refresh_tokens'} & set(inspect(engine).get_table_names()))

    run_migrations('head')
    inspector = inspect(engine)
    assert {'users', 'rooms', 'bookings', 'refresh_tokens', 'alembic_version'} <= set(inspector.get_table_names())
    assert 'ix_bookings_room_status_time_range' in {index['name'] for index in inspector.get_indexes('bookings')}
