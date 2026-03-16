from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.redis_client import delete_key, get_json, set_json
from app.models.room import Room
from app.schemas.room import RoomCreate

ROOMS_CACHE_KEY = 'rooms:all'


def list_rooms(db: Session) -> list[Room] | list[dict]:
    cached = get_json(ROOMS_CACHE_KEY)
    if cached is not None:
        return cached

    stmt = select(Room).order_by(Room.id.asc())
    rooms = list(db.execute(stmt).scalars().all())
    payload = [
        {
            'id': room.id,
            'name': room.name,
            'capacity': room.capacity,
            'location': room.location,
            'description': room.description,
            'created_at': room.created_at.isoformat(),
        }
        for room in rooms
    ]
    set_json(ROOMS_CACHE_KEY, payload, ttl_seconds=120)
    return rooms


def create_room(db: Session, payload: RoomCreate) -> Room:
    exists = db.execute(select(Room).where(Room.name == payload.name)).scalar_one_or_none()
    if exists is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='同名の会議室が既に存在します。')

    room = Room(
        name=payload.name,
        capacity=payload.capacity,
        location=payload.location,
        description=payload.description,
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    delete_key(ROOMS_CACHE_KEY)
    return room


def seed_default_rooms() -> None:
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        existing = db.execute(select(Room)).scalars().first()
        if existing is not None:
            return
        defaults = [
            Room(name='Tokyo-A', capacity=6, location='東京本社 3F', description='少人数向け会議室'),
            Room(name='Tokyo-B', capacity=10, location='東京本社 5F', description='標準会議室'),
            Room(name='Osaka-C', capacity=20, location='大阪支社 2F', description='大型会議向け'),
        ]
        db.add_all(defaults)
        db.commit()
    finally:
        db.close()
