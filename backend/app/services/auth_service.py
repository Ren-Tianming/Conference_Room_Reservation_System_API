from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.redis_client import blacklist_token
from app.core.security import create_token, decode_token, get_password_hash, verify_password
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.schemas.user import UserCreate
from app.services.user_service import get_user_by_username

logger = logging.getLogger(__name__)


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
    return user


def authenticate_user(db: Session, username: str, password: str) -> User:
    user = get_user_by_username(db, username)
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='ユーザー名またはパスワードが正しくありません。')
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='無効なユーザーです。')
    return user


def create_access_and_refresh_tokens(db: Session, user: User) -> TokenResponse:
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

    refresh_model = RefreshToken(user_id=user.id, token_jti=refresh_jti, expires_at=refresh_expire)
    db.add(refresh_model)
    db.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


def rotate_refresh_token(db: Session, refresh_token: str) -> TokenResponse:
    try:
        payload = decode_token(refresh_token)
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='無効なリフレッシュトークンです。') from exc

    if payload.get('type') != 'refresh':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='リフレッシュトークンが必要です。')

    user_id = payload.get('user_id')
    jti = payload.get('jti')
    if user_id is None or jti is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='トークン情報が不正です。')

    stmt = select(RefreshToken).where(RefreshToken.token_jti == jti, RefreshToken.user_id == user_id)
    stored = db.execute(stmt).scalar_one_or_none()
    if stored is None or stored.revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='このリフレッシュトークンは使用できません。')

    stored.revoked = True
    blacklist_token(jti, stored.expires_at)
    db.add(stored)
    db.commit()

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='ユーザーが存在しません。')

    return create_access_and_refresh_tokens(db, user)


def revoke_tokens(db: Session, *, access_token: str, refresh_token: Optional[str], user_id: int) -> None:
    try:
        access_payload = decode_token(access_token)
        access_jti = access_payload.get('jti')
        access_exp = access_payload.get('exp')
        access_user_id = access_payload.get('user_id')
        if access_jti and access_exp and access_user_id == user_id:
            blacklist_token(access_jti, datetime.fromtimestamp(access_exp, tz=timezone.utc))
    except Exception as exc:
        logger.warning('Failed to revoke access token for user_id=%s: %s', user_id, exc)

    if refresh_token:
        try:
            refresh_payload = decode_token(refresh_token)
            refresh_jti = refresh_payload.get('jti')
            refresh_user_id = refresh_payload.get('user_id')
            if refresh_jti and refresh_user_id == user_id:
                stmt = select(RefreshToken).where(RefreshToken.token_jti == refresh_jti, RefreshToken.user_id == user_id)
                stored = db.execute(stmt).scalar_one_or_none()
                if stored is not None:
                    stored.revoked = True
                    db.add(stored)
                    blacklist_token(refresh_jti, stored.expires_at)
                    db.commit()
        except Exception as exc:
            logger.warning('Failed to revoke refresh token for user_id=%s: %s', user_id, exc)
