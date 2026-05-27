from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.redis_client import get_redis_client
from app.core.security import decode_token
from app.db.session import SessionLocal
from app.main import app
from app.models.refresh_token import RefreshToken
from app.services.auth_service import hash_refresh_token
from tests.integration.helpers import register_and_login

pytestmark = pytest.mark.integration


def test_refresh_token_can_be_rotated_only_once_under_concurrency(client: TestClient) -> None:
    tokens = register_and_login(client, 'mysql-refresh-user')
    refresh_token = tokens['refresh_token']
    original_jti = decode_token(refresh_token)['jti']
    gate = Barrier(2)

    def rotate() -> int:
        gate.wait()
        with TestClient(app) as concurrent_client:
            response = concurrent_client.post('/api/v1/auth/refresh', json={'refresh_token': refresh_token})
            return response.status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = sorted(executor.map(lambda _: rotate(), range(2)))

    assert statuses == [200, 401]
    db = SessionLocal()
    try:
        assert db.scalar(select(func.count(RefreshToken.id))) == 2
        original = db.scalar(select(RefreshToken).where(RefreshToken.token_jti == original_jti))
        assert original is not None
        assert original.revoked is True
        assert original.token_hash == hash_refresh_token(refresh_token)
    finally:
        db.close()

    redis = get_redis_client()
    assert redis is not None
    assert redis.exists(f'blacklist:{original_jti}') == 1
