from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.redis_client import get_redis
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingRead
from app.schemas.common import MessageResponse
from app.services.booking_service import cancel_booking, create_booking, list_my_bookings

router = APIRouter()


@router.get('/me', response_model=list[BookingRead])
def get_my_bookings(
    status_filter: str | None = Query(default=None, alias='status'),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BookingRead]:
    return list_my_bookings(db, current_user.id, status_filter)


@router.post('', response_model=BookingRead, status_code=status.HTTP_201_CREATED)
def create_booking_endpoint(
    payload: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BookingRead:
    return create_booking(db, get_redis(), current_user, payload)


@router.delete('/{booking_id}', response_model=MessageResponse)
def cancel_booking_endpoint(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    cancel_booking(db, get_redis(), booking_id, current_user)
    return MessageResponse(message='预约已取消')
