from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.redis_client import room_lock
from app.models.booking import Booking
from app.models.room import Room
from app.models.user import User
from app.schemas.booking import BookingCreate


def list_my_bookings(db: Session, user_id: int) -> list[Booking]:
    stmt = (
        select(Booking)
        .options(selectinload(Booking.room))
        .where(Booking.user_id == user_id, Booking.status == 'active')
        .order_by(Booking.start_time.asc())
    )
    return list(db.execute(stmt).scalars().all())


def create_booking(db: Session, payload: BookingCreate, current_user: User) -> Booking:
    room = db.get(Room, payload.room_id)
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='会議室が存在しません。')

    if payload.attendee_count > room.capacity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='参加人数が会議室の定員を超えています。')

    with room_lock(payload.room_id):
        conflict_stmt = (
            select(Booking)
            .where(
                Booking.room_id == payload.room_id,
                Booking.status == 'active',
                Booking.start_time < payload.end_time,
                Booking.end_time > payload.start_time,
            )
            .with_for_update()
        )
        conflict = db.execute(conflict_stmt).scalars().first()
        if conflict is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='この時間帯は既に予約されています。')

        booking = Booking(
            user_id=current_user.id,
            room_id=payload.room_id,
            title=payload.title,
            purpose=payload.purpose,
            attendee_count=payload.attendee_count,
            start_time=payload.start_time,
            end_time=payload.end_time,
        )
        db.add(booking)
        db.commit()
        db.refresh(booking)
        return booking


def cancel_booking(db: Session, booking_id: int, user_id: int) -> None:
    stmt = select(Booking).where(Booking.id == booking_id, Booking.user_id == user_id, Booking.status == 'active')
    booking = db.execute(stmt).scalar_one_or_none()
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='予約が見つかりません。')

    booking.status = 'cancelled'
    db.add(booking)
    db.commit()
