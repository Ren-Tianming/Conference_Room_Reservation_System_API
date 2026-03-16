from datetime import date, datetime, time, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.redis_client import get_redis
from app.models.booking import Booking
from app.models.enums import BookingStatus
from app.models.room import ConferenceRoom
from app.schemas.room import RoomCreate, RoomRead, RoomScheduleItem, RoomScheduleResponse, RoomUpdate
from app.services.cache_service import (
    get_json_cache,
    invalidate_room_cache,
    room_list_cache_key,
    room_schedule_cache_key,
    set_json_cache,
)
from app.core.config import settings


def list_rooms(db: Session, include_inactive: bool = False) -> list[RoomRead]:
    redis_client = get_redis()
    cache_key = room_list_cache_key(include_inactive)
    cached = get_json_cache(redis_client, cache_key)
    if cached is not None:
        return [RoomRead.model_validate(item) for item in cached]

    stmt = select(ConferenceRoom).order_by(ConferenceRoom.id)
    if not include_inactive:
        stmt = stmt.where(ConferenceRoom.is_active.is_(True))

    rooms = db.execute(stmt).scalars().all()
    payload = [RoomRead.model_validate(room).model_dump(mode='json') for room in rooms]
    set_json_cache(redis_client, cache_key, payload, settings.room_cache_ttl_seconds)
    return [RoomRead.model_validate(item) for item in payload]


def create_room(db: Session, payload: RoomCreate) -> RoomRead:
    room = ConferenceRoom(**payload.model_dump())
    db.add(room)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='会议室名称已存在') from exc
    db.refresh(room)
    invalidate_room_cache(get_redis(), room.id)
    return RoomRead.model_validate(room)


def update_room(db: Session, room_id: int, payload: RoomUpdate) -> RoomRead:
    room = db.get(ConferenceRoom, room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='会议室不存在')

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(room, field, value)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='会议室更新失败，可能名称重复') from exc
    db.refresh(room)
    invalidate_room_cache(get_redis(), room.id)
    return RoomRead.model_validate(room)


def room_day_schedule(db: Session, room_id: int, day: date) -> RoomScheduleResponse:
    room = db.get(ConferenceRoom, room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='会议室不存在')

    redis_client = get_redis()
    cache_key = room_schedule_cache_key(room_id, day)
    cached = get_json_cache(redis_client, cache_key)
    if cached is not None:
        return RoomScheduleResponse.model_validate(cached)

    start_of_day = datetime.combine(day, time.min)
    end_of_day = start_of_day + timedelta(days=1)

    stmt = (
        select(Booking)
        .where(
            Booking.room_id == room_id,
            Booking.start_time < end_of_day,
            Booking.end_time > start_of_day,
            Booking.status == BookingStatus.CONFIRMED,
        )
        .order_by(Booking.start_time)
    )
    bookings = db.execute(stmt).scalars().all()
    response = RoomScheduleResponse(
        room_id=room.id,
        room_name=room.name,
        day=day.isoformat(),
        bookings=[
            RoomScheduleItem(
                booking_id=b.id,
                title=b.title,
                start_time=b.start_time,
                end_time=b.end_time,
                attendee_count=b.attendee_count,
                status=b.status.value,
            )
            for b in bookings
        ],
    )
    set_json_cache(redis_client, cache_key, response.model_dump(mode='json'), settings.room_schedule_cache_ttl_seconds)
    return response
