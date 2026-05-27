from __future__ import annotations

from sqlalchemy import inspect

from app.db.session import engine


def test_alembic_migration_creates_expected_tables(client) -> None:
    inspector = inspect(engine)
    assert set(inspector.get_table_names()) >= {
        'users',
        'rooms',
        'bookings',
        'refresh_tokens',
        'alembic_version',
    }
    assert {column['name'] for column in inspector.get_columns('users')} >= {
        'id',
        'username',
        'password_hash',
        'role',
        'is_active',
        'created_at',
    }
    assert {column['name'] for column in inspector.get_columns('bookings')} >= {
        'id',
        'title',
        'start_time',
        'end_time',
        'status',
        'user_id',
        'room_id',
    }
    assert {column['name'] for column in inspector.get_columns('refresh_tokens')} >= {
        'id',
        'token_jti',
        'token_hash',
        'expires_at',
        'revoked',
        'user_agent',
        'ip_address',
        'device_name',
        'user_id',
    }
    assert 'ix_refresh_tokens_token_hash' in {
        index['name'] for index in inspector.get_indexes('refresh_tokens')
    }
