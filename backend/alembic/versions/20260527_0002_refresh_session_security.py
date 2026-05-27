"""Add refresh token session security metadata.

Revision ID: 20260527_0002
Revises: 20260513_0001
Create Date: 2026-05-27
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '20260527_0002'
down_revision: str | None = '20260513_0001'
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('refresh_tokens', sa.Column('token_hash', sa.String(length=64), nullable=True))
    op.add_column('refresh_tokens', sa.Column('user_agent', sa.String(length=255), nullable=True))
    op.add_column('refresh_tokens', sa.Column('ip_address', sa.String(length=45), nullable=True))
    op.add_column('refresh_tokens', sa.Column('device_name', sa.String(length=100), nullable=True))
    op.create_index(op.f('ix_refresh_tokens_token_hash'), 'refresh_tokens', ['token_hash'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_refresh_tokens_token_hash'), table_name='refresh_tokens')
    op.drop_column('refresh_tokens', 'device_name')
    op.drop_column('refresh_tokens', 'ip_address')
    op.drop_column('refresh_tokens', 'user_agent')
    op.drop_column('refresh_tokens', 'token_hash')
