from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Optional, cast

from fastapi import HTTPException, status
from jwt.exceptions import InvalidTokenError
from redis.exceptions import RedisError
from sqlalchemy import delete, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.redis_client import blacklist_token, get_redis_client
from app.core.security import create_token, decode_token, get_password_hash, verify_password
from app.db.session import SessionLocal
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.schemas.user import UserCreate
from app.services.user_service import get_user_by_username

logger = logging.getLogger(__name__)
_failed_login_attempts: dict[str, tuple[int, float]] = {}


@dataclass(frozen=True)
class SessionMetadata:
    user_agent: str | None = None
    ip_address: str | None = None
    device_name: str | None = None


def hash_refresh_token(refresh_token: str) -> str:
    return sha256(refresh_token.encode('utf-8')).hexdigest()


def _cleanup_expired_refresh_tokens(db: Session) -> None:
    db.execute(delete(RefreshToken).where(RefreshToken.expires_at < datetime.now(timezone.utc)))


def cleanup_expired_refresh_tokens() -> int:
    db = SessionLocal()
    try:
        result = db.execute(delete(RefreshToken).where(RefreshToken.expires_at < datetime.now(timezone.utc)))
        db.commit()
        return int(result.rowcount or 0)
    except Exception:
        db.rollback()
        logger.exception('Periodic refresh token cleanup failed.')
        return 0
    finally:
        db.close()


def _rate_limit_key(username: str) -> str:
    return f"auth:failed-login:{username.lower()}"


def _is_login_rate_limited(username: str) -> bool:
    key = _rate_limit_key(username)
    client = get_redis_client()
    if client is not None:
        try:
            redis_count = cast(Optional[str], client.get(key))
            return redis_count is not None and int(redis_count) >= settings.auth_rate_limit_max_attempts
        except RedisError as exc:
            logger.warning("Failed to check login rate limit for username=%s: %s", username, exc)

    now = time.monotonic()
    count, expires_at = _failed_login_attempts.get(key, (0, 0))
    if now >= expires_at:
        _failed_login_attempts.pop(key, None)
        return False
    return count >= settings.auth_rate_limit_max_attempts


def _record_failed_login(username: str) -> None:
    key = _rate_limit_key(username)
    client = get_redis_client()
    if client is not None:
        try:
            count = client.incr(key)
            if count == 1:
                client.expire(key, settings.auth_rate_limit_window_seconds)
            return
        except RedisError as exc:
            logger.warning("Failed to record login rate limit for username=%s: %s", username, exc)

    now = time.monotonic()
    count, expires_at = _failed_login_attempts.get(key, (0, now + settings.auth_rate_limit_window_seconds))
    if now >= expires_at:
        count = 0
        expires_at = now + settings.auth_rate_limit_window_seconds
    _failed_login_attempts[key] = (count + 1, expires_at)


def _clear_failed_logins(username: str) -> None:
    key = _rate_limit_key(username)
    client = get_redis_client()
    if client is not None:
        try:
            client.delete(key)
            return
        except RedisError as exc:
            logger.warning("Failed to clear login rate limit for username=%s: %s", username, exc)
    _failed_login_attempts.pop(key, None)


def register_user(db: Session, payload: UserCreate) -> User:
    exists = get_user_by_username(db, payload.username)
    if exists is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='このユーザー名は既に使用されています。')

    user = User(username=payload.username, password_hash=get_password_hash(payload.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='このユーザー名は既に使用されています。') from exc
    db.refresh(user)
    logger.info("User registered: user_id=%s username=%s", user.id, user.username)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User:
    if _is_login_rate_limited(username):
        logger.warning("Login rate limit exceeded for username=%s", username)
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail='ログイン試行回数が多すぎます。しばらくしてから再試行してください。')

    user = get_user_by_username(db, username)
    if user is None or not verify_password(password, user.password_hash):
        _record_failed_login(username)
        logger.warning("Failed login attempt for username=%s", username)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='ユーザー名またはパスワードが正しくありません。')
    if not user.is_active:
        logger.warning("Inactive user login attempt: user_id=%s username=%s", user.id, user.username)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='無効なユーザーです。')
    _clear_failed_logins(username)
    logger.info("User authenticated: user_id=%s username=%s", user.id, user.username)
    return user


def create_access_and_refresh_tokens(
    db: Session,
    user: User,
    metadata: SessionMetadata | None = None,
) -> TokenResponse:
    metadata = metadata or SessionMetadata()
    _cleanup_expired_refresh_tokens(db)
    access_token, _, _ = create_token(
        user_id=user.id,
        token_type='access',
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    refresh_token, refresh_jti, refresh_expire = create_token(
        user_id=user.id,
        token_type='refresh',
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )

    refresh_model = RefreshToken(
        user_id=user.id,
        token_jti=refresh_jti,
        token_hash=hash_refresh_token(refresh_token),
        expires_at=refresh_expire,
        user_agent=metadata.user_agent,
        ip_address=metadata.ip_address,
        device_name=metadata.device_name,
    )
    db.add(refresh_model)
    db.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


def rotate_refresh_token(
    db: Session,
    refresh_token: str,
    metadata: SessionMetadata | None = None,
) -> TokenResponse:
    try:
        payload = decode_token(refresh_token)
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='無効なリフレッシュトークンです。') from exc

    if payload.get('type') != 'refresh':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='リフレッシュトークンが必要です。')

    user_id = payload.get('user_id')
    jti = payload.get('jti')
    if user_id is None or jti is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='トークン情報が不正です。')

    revoke_stmt = (
        update(RefreshToken)
        .where(
            RefreshToken.token_jti == jti,
            RefreshToken.user_id == user_id,
            RefreshToken.revoked.is_(False),
            or_(
                RefreshToken.token_hash == hash_refresh_token(refresh_token),
                RefreshToken.token_hash.is_(None),
            ),
        )
        .values(revoked=True)
    )
    result = db.execute(revoke_stmt)
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='このリフレッシュトークンは使用できません。')

    stmt = select(RefreshToken).where(RefreshToken.token_jti == jti, RefreshToken.user_id == user_id)
    stored = db.execute(stmt).scalar_one()
    blacklist_token(jti, stored.expires_at)
    db.commit()

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='ユーザーが存在しません。')

    return create_access_and_refresh_tokens(db, user, metadata)


def revoke_tokens(db: Session, *, access_token: str, refresh_token: Optional[str], user_id: int) -> None:
    try:
        access_payload = decode_token(access_token)
        access_jti = access_payload.get('jti')
        access_exp = access_payload.get('exp')
        access_user_id = access_payload.get('user_id')
        if access_jti and access_exp and access_user_id == user_id:
            blacklist_token(access_jti, datetime.fromtimestamp(access_exp, tz=timezone.utc))
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning('Failed to revoke access token for user_id=%s: %s', user_id, exc)

    if refresh_token:
        try:
            refresh_payload = decode_token(refresh_token)
            refresh_jti = refresh_payload.get('jti')
            refresh_user_id = refresh_payload.get('user_id')
            if refresh_jti and refresh_user_id == user_id:
                stmt = select(RefreshToken).where(
                    RefreshToken.token_jti == refresh_jti,
                    RefreshToken.user_id == user_id,
                    or_(
                        RefreshToken.token_hash == hash_refresh_token(refresh_token),
                        RefreshToken.token_hash.is_(None),
                    ),
                )
                stored = db.execute(stmt).scalar_one_or_none()
                if stored is not None:
                    stored.revoked = True
                    db.add(stored)
                    blacklist_token(refresh_jti, stored.expires_at)
                    db.commit()
        except HTTPException:
            raise
        except Exception as exc:
            logger.warning('Failed to revoke refresh token for user_id=%s: %s', user_id, exc)


def revoke_all_tokens(db: Session, *, access_token: str, user_id: int) -> int:
    revoke_tokens(db, access_token=access_token, refresh_token=None, user_id=user_id)
    stmt = select(RefreshToken).where(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked.is_(False),
    )
    stored_tokens = list(db.execute(stmt).scalars().all())
    for stored in stored_tokens:
        stored.revoked = True
        db.add(stored)
        blacklist_token(stored.token_jti, stored.expires_at)
    db.commit()
    return len(stored_tokens)
