from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin_user
from app.models.user import User
from app.schemas.room import RoomCreate, RoomRead
from app.services.room_service import create_room, list_rooms

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get('', response_model=list[RoomRead])
def read_rooms(db: Session = Depends(get_db)) -> list[RoomRead]:
    return list_rooms(db)


@router.post('', response_model=RoomRead, status_code=status.HTTP_201_CREATED)
def create_new_room(
    payload: RoomCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin_user),
) -> RoomRead:
    room = create_room(db, payload)
    logger.info(
        'Administrator created room.',
        extra={
            'event': 'admin_room_created',
            'user_id': current_admin.id,
            'room_id': room.id,
        },
    )
    return RoomRead.model_validate(room)
