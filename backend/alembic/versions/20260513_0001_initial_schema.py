"""initial schema

Revision ID: 20260513_0001
Revises:
Create Date: 2026-05-13 00:00:00.000000
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = '20260513_0001'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=64), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("role IN ('user', 'admin')", name='ck_users_role'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)

    op.create_table(
        'rooms',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('capacity', sa.Integer(), nullable=False),
        sa.Column('location', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('capacity > 0', name='ck_rooms_capacity_positive'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_rooms_name'), 'rooms', ['name'], unique=True)

    op.create_table(
        'bookings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=100), nullable=False),
        sa.Column('purpose', sa.String(length=255), nullable=True),
        sa.Column('attendee_count', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('room_id', sa.Integer(), nullable=False),
        sa.CheckConstraint('end_time > start_time', name='ck_bookings_time_range'),
        sa.CheckConstraint("status IN ('active', 'cancelled', 'completed')", name='ck_bookings_status'),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_bookings_start_time'), 'bookings', ['start_time'], unique=False)
    op.create_index(op.f('ix_bookings_end_time'), 'bookings', ['end_time'], unique=False)
    op.create_index(op.f('ix_bookings_user_id'), 'bookings', ['user_id'], unique=False)
    op.create_index(op.f('ix_bookings_room_id'), 'bookings', ['room_id'], unique=False)
    op.create_index('ix_bookings_room_status_time_range', 'bookings', ['room_id', 'status', 'start_time', 'end_time'], unique=False)

    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token_jti', sa.String(length=64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_refresh_tokens_token_jti'), 'refresh_tokens', ['token_jti'], unique=True)
    op.create_index(op.f('ix_refresh_tokens_user_id'), 'refresh_tokens', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_refresh_tokens_user_id'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_token_jti'), table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
    op.drop_index('ix_bookings_room_status_time_range', table_name='bookings')
    op.drop_index(op.f('ix_bookings_room_id'), table_name='bookings')
    op.drop_index(op.f('ix_bookings_user_id'), table_name='bookings')
    op.drop_index(op.f('ix_bookings_end_time'), table_name='bookings')
    op.drop_index(op.f('ix_bookings_start_time'), table_name='bookings')
    op.drop_table('bookings')
    op.drop_index(op.f('ix_rooms_name'), table_name='rooms')
    op.drop_table('rooms')
    op.drop_index(op.f('ix_users_role'), table_name='users')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_table('users')
