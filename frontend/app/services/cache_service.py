import json
from datetime import date

from fastapi.encoders import jsonable_encoder
from redis import Redis

from app.core.config import settings


def room_list_cache_key(include_inactive: bool) -> str:
    return f'cache:rooms:list:{int(include_inactive)}'


def room_schedule_cache_key(room_id: int, day: date) -> str:
    return f'cache:rooms:{room_id}:schedule:{day.isoformat()}'


def get_json_cache(redis_client: Redis, key: str):
    data = redis_client.get(key)
    if not data:
        return None
    return json.loads(data)


def set_json_cache(redis_client: Redis, key: str, value: dict | list, ttl_seconds: int) -> None:
    redis_client.setex(key, ttl_seconds, json.dumps(jsonable_encoder(value), ensure_ascii=False))


def invalidate_room_cache(redis_client: Redis, room_id: int | None = None) -> None:
    redis_client.delete(room_list_cache_key(True), room_list_cache_key(False))
    if room_id is not None:
        pattern = room_schedule_cache_key(room_id, date.today()).rsplit(':', 1)[0] + ':*'
        for key in redis_client.scan_iter(match=pattern):
            redis_client.delete(key)
