from __future__ import annotations

import json
import logging
from contextlib import contextmanager
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Iterator, Optional, Union, cast

from fastapi import HTTPException, status
from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings

logger = logging.getLogger(__name__)
_SENTINEL = object()
_cached_client: Union[Redis, object, None] = _SENTINEL
_fallback_locks_guard = Lock()
_fallback_room_locks: dict[int, Lock] = {}


class ProcessLocalRoomLock:
    def __init__(self, room_id: int) -> None:
        self.room_id = room_id
        self._lock = self._get_lock(room_id)

    @staticmethod
    def _get_lock(room_id: int) -> Lock:
        with _fallback_locks_guard:
            return _fallback_room_locks.setdefault(room_id, Lock())

    def __enter__(self):
        self._lock.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._lock.release()
        return False


def get_redis_client() -> Optional[Redis]:
    global _cached_client
    if _cached_client is not _SENTINEL and _cached_client is not None:
        return _cached_client  # type: ignore[return-value]
    try:
        client = Redis.from_url(settings.redis_url, decode_responses=True)
        client.ping()
        _cached_client = client
        return client
    except Exception as exc:
        logger.warning('Redis is unavailable: %s', exc)
        _cached_client = None
        return None


def set_json(key: str, value: Any, ttl_seconds: int = 60) -> None:
    client = get_redis_client()
    if client is None:
        return
    try:
        client.setex(key, ttl_seconds, json.dumps(value, default=str))
    except RedisError as exc:
        logger.warning('Failed to set Redis JSON cache for %s: %s', key, exc)


def get_json(key: str) -> Optional[Any]:
    client = get_redis_client()
    if client is None:
        return None
    try:
        value = cast(Optional[str], client.get(key))
        if value is None:
            return None
        return json.loads(value)
    except (RedisError, json.JSONDecodeError) as exc:
        logger.warning('Failed to get Redis JSON cache for %s: %s', key, exc)
        return None


def delete_key(key: str) -> None:
    client = get_redis_client()
    if client is None:
        return
    try:
        client.delete(key)
    except RedisError as exc:
        logger.warning('Failed to delete Redis key %s: %s', key, exc)


def blacklist_token(jti: str, expires_at: datetime) -> None:
    client = get_redis_client()
    if client is None:
        if settings.require_redis_for_token_blacklist:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail='Redis が利用できないためトークンを無効化できません。')
        return
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    ttl = max(int((expires_at - datetime.now(timezone.utc)).total_seconds()), 1)
    try:
        client.setex(f"blacklist:{jti}", ttl, "1")
    except RedisError as exc:
        logger.warning('Failed to blacklist token %s: %s', jti, exc)
        if settings.require_redis_for_token_blacklist:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail='トークン無効化に失敗しました。') from exc


def is_token_blacklisted(jti: str) -> bool:
    client = get_redis_client()
    if client is None:
        if settings.require_redis_for_token_blacklist:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail='Redis が利用できないためトークン状態を確認できません。')
        return False
    try:
        return bool(client.exists(f"blacklist:{jti}"))
    except RedisError as exc:
        logger.warning('Failed to check token blacklist for %s: %s', jti, exc)
        if settings.require_redis_for_token_blacklist:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail='トークン状態確認に失敗しました。') from exc
        return False


@contextmanager
def room_lock(room_id: int) -> Iterator[object]:
    client = get_redis_client()
    if client is None:
        if settings.require_redis_for_locks:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail='Redis が利用できないため予約ロックを取得できません。')
        logger.warning('Using process-local room lock for room_id=%s because Redis is unavailable.', room_id)
        with ProcessLocalRoomLock(room_id) as lock:
            yield lock
        return

    lock = client.lock(f"lock:room:{room_id}", timeout=10, blocking_timeout=3)
    acquired = False
    try:
        acquired = lock.acquire(blocking=True)
        if not acquired:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='予約処理が混雑しています。再試行してください。')
        yield lock
    finally:
        if acquired:
            try:
                lock.release()
            except RedisError as exc:
                logger.warning('Failed to release room lock for room_id=%s: %s', room_id, exc)
