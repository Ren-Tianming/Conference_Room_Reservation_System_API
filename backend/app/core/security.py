from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_token(*, user_id: int, token_type: str, expires_delta: timedelta) -> tuple[str, str, datetime]:
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    jti = str(uuid4())
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "user_id": user_id,
        "type": token_type,
        "jti": jti,
        "iat": now,
        "exp": expire,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
    }
    encoded = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return encoded, jti, expire


def decode_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm],
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
    )
