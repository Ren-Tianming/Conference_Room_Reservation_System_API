from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, Integer, CheckConstraint
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from sqlalchemy.sql import func

if TYPE_CHECKING:
    from .bookings import Booking


class Base(DeclarativeBase):
    pass


class ConferenceRoom(Base):
    __tablename__ = "conference_rooms"

    __table_args__ = (
        CheckConstraint("capacity > 0", name="check_capacity_positive"),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="会議室ID"
    )

    name: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        index=True,
        nullable=False,
        comment="会議室名"
    )

    capacity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="会議室定員"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        comment="作成時間"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新時間"
    )

    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="conferenceroom",
        cascade="all, delete-orphan"
    )