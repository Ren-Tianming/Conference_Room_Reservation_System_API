from sql_app.database import Base
from sqlalchemy import ForeignKey, String, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime

class User(Base):
    __tablename__ = 'users'
    user_id: Mapped[int] = mapped_column(primary_key=True)
    user_name: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

class ConferenceRoom(Base):
    __tablename__ = "conferencerooms"

    conferenceroom_id: Mapped[int] = mapped_column(primary_key=True)
    conferenceroom_name: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    conferenceroom_capacity: Mapped[int] = mapped_column(nullable=False)

    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="conferenceroom"
    )

class Booking(Base):
    __tablename__ = "bookings"

    booking_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False
    )
    conferenceroom_id: Mapped[int] = mapped_column(
        ForeignKey("conferencerooms.conferenceroom_id", ondelete="RESTRICT"),
        nullable=False
    )

    booking_capacity: Mapped[int] = mapped_column(nullable=False)
    start_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    user: Mapped["User"] = relationship(back_populates="bookings")
    conferenceroom: Mapped["ConferenceRoom"] = relationship(back_populates="bookings")