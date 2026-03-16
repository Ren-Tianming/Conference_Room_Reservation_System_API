from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user, get_current_user, get_db
from app.models.user import User
from app.schemas.room import RoomCreate, RoomRead, RoomScheduleResponse, RoomUpdate
from app.services.room_service import create_room, list_rooms, room_day_schedule, update_room

router = APIRouter()


@router.get('', response_model=list[RoomRead])
def get_rooms(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[RoomRead]:
    return list_rooms(db, include_inactive=include_inactive)


@router.post('', response_model=RoomRead, status_code=status.HTTP_201_CREATED)
def create_room_endpoint(
    payload: RoomCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
) -> RoomRead:
    return create_room(db, payload)


@router.patch('/{room_id}', response_model=RoomRead)
def update_room_endpoint(
    room_id: int,
    payload: RoomUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
) -> RoomRead:
    return update_room(db, room_id, payload)


@router.get('/{room_id}/schedule', response_model=RoomScheduleResponse)
def get_room_schedule(
    room_id: int,
    day: date = Query(..., description='查询哪一天的排期，例如 2026-03-16'),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> RoomScheduleResponse:
    return room_day_schedule(db, room_id, day)
