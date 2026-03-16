from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import BookingStatus


class Booking(Base):
    __tablename__ = 'bookings'
    __table_args__ = (
        CheckConstraint('attendee_count > 0', name='ck_booking_attendee_count_positive'),
        CheckConstraint('start_time < end_time', name='ck_booking_time_range_valid'),
        Index('ix_bookings_room_time', 'room_id', 'start_time', 'end_time'),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='RESTRICT'), nullable=False)
    room_id: Mapped[int] = mapped_column(ForeignKey('conference_rooms.id', ondelete='RESTRICT'), nullable=False)

    attendee_count: Mapped[int] = mapped_column(nullable=False)
    start_time: Mapped[datetime] = mapped_column(nullable=False)
    end_time: Mapped[datetime] = mapped_column(nullable=False)
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus),
        default=BookingStatus.CONFIRMED,
        nullable=False,
    )

    user: Mapped['User'] = relationship(back_populates='bookings')
    room: Mapped['ConferenceRoom'] = relationship(back_populates='bookings')
