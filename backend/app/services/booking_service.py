from uuid import uuid4

from fastapi import HTTPException, status
from redis import Redis
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.booking import Booking
from app.models.enums import BookingStatus
from app.models.room import ConferenceRoom
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingRead
from app.services.cache_service import invalidate_room_cache

RELEASE_LOCK_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
else
    return 0
end
"""


def _acquire_room_lock(redis_client: Redis, room_id: int) -> tuple[str, str]:
    lock_key = f'lock:booking:room:{room_id}'
    lock_value = str(uuid4())
    locked = redis_client.set(lock_key, lock_value, nx=True, ex=settings.booking_lock_ttl_seconds)
    if not locked:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='当前会议室有并发预约请求，请稍后重试',
        )
    return lock_key, lock_value


def _release_lock(redis_client: Redis, lock_key: str, lock_value: str) -> None:
    try:
        redis_client.eval(RELEASE_LOCK_SCRIPT, 1, lock_key, lock_value)
    except Exception:
        pass


def list_my_bookings(db: Session, user_id: int, status_filter: str | None = None) -> list[BookingRead]:
    stmt = select(Booking).where(Booking.user_id == user_id).order_by(Booking.start_time.desc())
    if status_filter:
        stmt = stmt.where(Booking.status == status_filter)
    bookings = db.execute(stmt).scalars().all()
    return [BookingRead.model_validate(item) for item in bookings]


def create_booking(db: Session, redis_client: Redis, current_user: User, payload: BookingCreate) -> BookingRead:
    lock_key, lock_value = _acquire_room_lock(redis_client, payload.room_id)
    try:
        room_stmt = (
            select(ConferenceRoom)
            .where(ConferenceRoom.id == payload.room_id, ConferenceRoom.is_active.is_(True))
            .with_for_update()
        )
        room = db.execute(room_stmt).scalar_one_or_none()
        if not room:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='会议室不存在或已停用')

        if payload.attendee_count > room.capacity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'参会人数不能超过会议室容量 {room.capacity}',
            )

        conflict_stmt = select(Booking).where(
            Booking.room_id == payload.room_id,
            Booking.status == BookingStatus.CONFIRMED,
            Booking.start_time < payload.end_time,
            Booking.end_time > payload.start_time,
        )
        conflict_booking = db.execute(conflict_stmt).scalar_one_or_none()
        if conflict_booking:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='该时间段已被预约')

        booking = Booking(
            title=payload.title,
            description=payload.description,
            user_id=current_user.id,
            room_id=payload.room_id,
            attendee_count=payload.attendee_count,
            start_time=payload.start_time,
            end_time=payload.end_time,
            status=BookingStatus.CONFIRMED,
        )
        db.add(booking)
        db.commit()
        db.refresh(booking)
        invalidate_room_cache(redis_client, payload.room_id)
        return BookingRead.model_validate(booking)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='预约创建失败') from exc
    finally:
        _release_lock(redis_client, lock_key, lock_value)


def cancel_booking(db: Session, redis_client: Redis, booking_id: int, current_user: User) -> None:
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='预约不存在')
    if booking.user_id != current_user.id and current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='无权取消他人预约')
    if booking.status == BookingStatus.CANCELLED:
        return

    booking.status = BookingStatus.CANCELLED
    db.commit()
    invalidate_room_cache(redis_client, booking.room_id)
