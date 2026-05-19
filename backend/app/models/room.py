from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Room(Base):
    __tablename__ = 'rooms'
    __table_args__ = (
        CheckConstraint('capacity > 0', name='ck_rooms_capacity_positive'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    capacity: Mapped[int] = mapped_column(Integer)
    location: Mapped[str] = mapped_column(String(100), default='本社')
    description: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    bookings = relationship('Booking', back_populates='room', cascade='all, delete-orphan')
