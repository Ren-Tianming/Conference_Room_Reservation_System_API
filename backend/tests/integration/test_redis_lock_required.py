from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.redis_client import get_redis_client
from tests.integration.helpers import auth_header, create_room, promote_to_admin, register_and_login

pytestmark = pytest.mark.integration


def test_ready_uses_running_redis_service(client: TestClient) -> None:
    response = client.get('/api/v1/ready')
    assert response.status_code == 200
    assert response.json() == {'status': 'ready', 'database': 'ok', 'redis': 'ok'}
    assert get_redis_client() is not None


def test_ready_returns_503_when_required_redis_is_unavailable(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr('app.api.routes.health.get_redis_client', lambda: None)

    response = client.get('/api/v1/ready')

    assert response.status_code == 503
    assert response.json() == {'status': 'not_ready', 'database': 'ok', 'redis': 'unavailable'}


def test_booking_fails_closed_when_required_redis_lock_is_unavailable(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tokens = register_and_login(client, 'redis-required-user')
    promote_to_admin('redis-required-user')
    room_id = create_room(client, tokens, name='Lock-Required-Room')
    start = datetime.now(timezone.utc) + timedelta(days=1)
    payload = {
        'room_id': room_id,
        'title': 'Lock required',
        'purpose': None,
        'attendee_count': 2,
        'start_time': start.isoformat(),
        'end_time': (start + timedelta(minutes=30)).isoformat(),
    }

    monkeypatch.setattr('app.api.deps.is_token_blacklisted', lambda _jti: False)
    monkeypatch.setattr('app.core.redis_client.get_redis_client', lambda: None)

    response = client.post('/api/v1/bookings', json=payload, headers=auth_header(tokens))

    assert response.status_code == 503
    assert '予約ロック' in response.json()['detail']
