from datetime import UTC, datetime

import jwt
from fastapi import HTTPException, status
from redis import Redis
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.user import UserCreate


def register_user(db: Session, payload: UserCreate) -> User:
    existing_user = db.execute(
        select(User).where(or_(User.username == payload.username, User.email == payload.email))
    ).scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='用户名或邮箱已存在')

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='用户创建失败，数据重复') from exc
    db.refresh(user)
    return user


def authenticate_user(db: Session, login_name: str, password: str) -> User | None:
    user = db.execute(
        select(User).where(or_(User.username == login_name, User.email == login_name))
    ).scalar_one_or_none()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None
    return user


def _store_refresh_token(redis_client: Redis, jti: str, user_id: int, expires_at: datetime) -> None:
    ttl = max(int((expires_at - datetime.now(UTC)).total_seconds()), 1)
    redis_client.setex(f'auth:refresh:{jti}', ttl, str(user_id))


def _blacklist_access_token(redis_client: Redis, jti: str, expires_at: datetime) -> None:
    ttl = max(int((expires_at - datetime.now(UTC)).total_seconds()), 1)
    redis_client.setex(f'auth:blacklist:{jti}', ttl, '1')


def issue_token_pair(user: User, redis_client: Redis) -> dict:
    access_token, access_jti, access_expires_at = create_access_token(str(user.id))
    refresh_token, refresh_jti, refresh_expires_at = create_refresh_token(str(user.id))
    _store_refresh_token(redis_client, refresh_jti, user.id, refresh_expires_at)
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'access_token_expires_at': access_expires_at,
        'refresh_token_expires_at': refresh_expires_at,
    }


def refresh_access_token(db: Session, redis_client: Redis, refresh_token: str) -> tuple[User, dict]:
    try:
        payload = decode_token(refresh_token)
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='refresh token 无效') from exc

    if payload.get('type') != 'refresh':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='token 类型错误')

    user_id = payload.get('sub')
    jti = payload.get('jti')
    if not user_id or not jti:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='refresh token 缺少必要字段')

    key = f'auth:refresh:{jti}'
    if redis_client.get(key) != str(user_id):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='refresh token 已失效')

    user = db.get(User, int(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='用户不存在或已被禁用')

    redis_client.delete(key)
    return user, issue_token_pair(user, redis_client)


def logout_tokens(redis_client: Redis, access_token: str, refresh_token: str | None = None) -> None:
    try:
        access_payload = decode_token(access_token)
        access_jti = access_payload.get('jti')
        access_exp = access_payload.get('exp')
        if access_jti and access_exp:
            expires_at = datetime.fromtimestamp(access_exp, tz=UTC)
            _blacklist_access_token(redis_client, access_jti, expires_at)
    except jwt.InvalidTokenError:
        pass

    if refresh_token:
        try:
            refresh_payload = decode_token(refresh_token)
            refresh_jti = refresh_payload.get('jti')
            if refresh_jti:
                redis_client.delete(f'auth:refresh:{refresh_jti}')
        except jwt.InvalidTokenError:
            pass
