from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings

_SENTINEL = object()
_cached_client: Redis | None | object = _SENTINEL


class DummyLock:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False



def get_redis_client() -> Redis | None:
    global _cached_client
    if _cached_client is not _SENTINEL and _cached_client is not None:
        return _cached_client  # type: ignore[return-value]
    try:
        client = Redis.from_url(settings.redis_url, decode_responses=True)
        client.ping()
        _cached_client = client
        return client
    except Exception:
        _cached_client = None
        return None


def set_json(key: str, value: Any, ttl_seconds: int = 60) -> None:
    client = get_redis_client()
    if client is None:
        return
    try:
        client.setex(key, ttl_seconds, json.dumps(value, default=str))
    except RedisError:
        return


def get_json(key: str) -> Any | None:
    client = get_redis_client()
    if client is None:
        return None
    try:
        value = client.get(key)
        if value is None:
            return None
        return json.loads(value)
    except (RedisError, json.JSONDecodeError):
        return None


def delete_key(key: str) -> None:
    client = get_redis_client()
    if client is None:
        return
    try:
        client.delete(key)
    except RedisError:
        return


def blacklist_token(jti: str, expires_at: datetime) -> None:
    client = get_redis_client()
    if client is None:
        return
    ttl = max(int((expires_at - datetime.now(timezone.utc)).total_seconds()), 1)
    try:
        client.setex(f"blacklist:{jti}", ttl, "1")
    except RedisError:
        return


def is_token_blacklisted(jti: str) -> bool:
    client = get_redis_client()
    if client is None:
        return False
    try:
        return bool(client.exists(f"blacklist:{jti}"))
    except RedisError:
        return False


@contextmanager
def room_lock(room_id: int) -> Iterator[object]:
    client = get_redis_client()
    if client is None:
        yield DummyLock()
        return

    lock = client.lock(f"lock:room:{room_id}", timeout=10, blocking_timeout=3)
    acquired = False
    try:
        acquired = lock.acquire(blocking=True)
        yield lock
    finally:
        if acquired:
            try:
                lock.release()
            except RedisError:
                pass
