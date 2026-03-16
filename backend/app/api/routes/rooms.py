from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.room import RoomCreate, RoomRead
from app.services.room_service import create_room, list_rooms

router = APIRouter()


@router.get('', response_model=list[RoomRead])
def read_rooms(db: Session = Depends(get_db)) -> list[RoomRead]:
    rooms = list_rooms(db)
    return [RoomRead.model_validate(room) for room in rooms]


@router.post('', response_model=RoomRead, status_code=status.HTTP_201_CREATED)
def create_new_room(
    payload: RoomCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> RoomRead:
    room = create_room(db, payload)
    return RoomRead.model_validate(room)
