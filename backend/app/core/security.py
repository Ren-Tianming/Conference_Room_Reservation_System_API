from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


def create_token(subject: str, expires_delta: timedelta, token_type: str) -> tuple[str, str, datetime]:
    expire_at = datetime.now(UTC) + expires_delta
    jti = str(uuid4())
    payload = {
        'sub': subject,
        'type': token_type,
        'jti': jti,
        'exp': expire_at,
        'iat': datetime.now(UTC),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, jti, expire_at


def create_access_token(subject: str) -> tuple[str, str, datetime]:
    return create_token(
        subject=subject,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        token_type='access',
    )


def create_refresh_token(subject: str) -> tuple[str, str, datetime]:
    return create_token(
        subject=subject,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
        token_type='refresh',
    )


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
