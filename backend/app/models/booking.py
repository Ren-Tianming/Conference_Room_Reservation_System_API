from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class BookingStatus(str, Enum):
    ACTIVE = 'active'
    CANCELLED = 'cancelled'
    COMPLETED = 'completed'


class Booking(Base):
    __tablename__ = 'bookings'
    __table_args__ = (
        CheckConstraint('end_time > start_time', name='ck_bookings_time_range'),
        CheckConstraint("status IN ('active', 'cancelled', 'completed')", name='ck_bookings_status'),
        Index('ix_bookings_room_status_time_range', 'room_id', 'status', 'start_time', 'end_time'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    purpose: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    attendee_count: Mapped[int] = mapped_column(Integer)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(20), default=BookingStatus.ACTIVE.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    room_id: Mapped[int] = mapped_column(ForeignKey('rooms.id', ondelete='CASCADE'), index=True)

    user = relationship('User', back_populates='bookings')
    room = relationship('Room', back_populates='bookings')
