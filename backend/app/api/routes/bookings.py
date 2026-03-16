from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingRead
from app.services.booking_service import cancel_booking, create_booking, list_my_bookings

router = APIRouter()


@router.get('/me', response_model=list[BookingRead])
def read_my_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BookingRead]:
    bookings = list_my_bookings(db, current_user.id)
    return [BookingRead.model_validate(item) for item in bookings]


@router.post('', response_model=BookingRead, status_code=status.HTTP_201_CREATED)
def create_new_booking(
    payload: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BookingRead:
    booking = create_booking(db, payload, current_user)
    return BookingRead.model_validate(booking)


@router.delete('/{booking_id}', status_code=status.HTTP_200_OK)
def delete_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    cancel_booking(db, booking_id, current_user.id)
    return {"message": "予約をキャンセルしました。"}
