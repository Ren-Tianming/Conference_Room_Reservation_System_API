from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
import jwt
from sqlalchemy import select

from app.core.config import settings
from app.core.security import decode_token
from app.db.session import SessionLocal
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole
from app.services.auth_service import cleanup_expired_refresh_tokens, hash_refresh_token


def register_and_login(client: TestClient, username: str = 'alice') -> dict[str, str]:
    response = client.post('/api/v1/auth/register', json={'username': username, 'password': 'password123'})
    assert response.status_code == 201
    login = client.post('/api/v1/auth/login', json={'username': username, 'password': 'password123'})
    assert login.status_code == 200
    return login.json()


def auth_header(tokens: dict[str, str]) -> dict[str, str]:
    return {'Authorization': f"Bearer {tokens['access_token']}"}


def promote_to_admin(username: str) -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).one()
        user.role = UserRole.ADMIN.value
        db.add(user)
        db.commit()
    finally:
        db.close()


def test_user_registration_login_and_me(client: TestClient) -> None:
    tokens = register_and_login(client)
    response = client.get('/api/v1/users/me', headers=auth_header(tokens))
    assert response.status_code == 200
    assert response.json()['username'] == 'alice'
    assert response.json()['role'] == UserRole.USER.value


def test_user_registration_returns_created_user(client: TestClient) -> None:
    response = client.post('/api/v1/auth/register', json={'username': 'new-user', 'password': 'password123'})
    assert response.status_code == 201
    body = response.json()
    assert body['username'] == 'new-user'
    assert body['role'] == UserRole.USER.value
    assert 'password' not in body
    assert 'password_hash' not in body


def test_user_login_returns_access_and_refresh_tokens(client: TestClient) -> None:
    created = client.post('/api/v1/auth/register', json={'username': 'login-user', 'password': 'password123'})
    assert created.status_code == 201
    response = client.post('/api/v1/auth/login', json={'username': 'login-user', 'password': 'password123'})
    assert response.status_code == 200
    assert response.json()['token_type'] == 'bearer'
    assert response.json()['access_token']
    assert response.json()['refresh_token']


def test_refresh_token_is_hashed_and_tracks_session_metadata(client: TestClient) -> None:
    created = client.post('/api/v1/auth/register', json={'username': 'device-user', 'password': 'password123'})
    assert created.status_code == 201
    response = client.post(
        '/api/v1/auth/login',
        json={'username': 'device-user', 'password': 'password123'},
        headers={'user-agent': 'ConferenceDesktop/1.0', 'x-device-name': 'Desk Laptop'},
    )
    assert response.status_code == 200
    refresh_token = response.json()['refresh_token']

    db = SessionLocal()
    try:
        stored = db.scalar(select(RefreshToken))
        assert stored is not None
        assert stored.token_hash == hash_refresh_token(refresh_token)
        assert stored.token_hash != refresh_token
        assert stored.user_agent == 'ConferenceDesktop/1.0'
        assert stored.device_name == 'Desk Laptop'
        assert stored.ip_address is not None
    finally:
        db.close()


def test_login_rate_limit_after_repeated_failures(client: TestClient) -> None:
    created = client.post('/api/v1/auth/register', json={'username': 'limited-user', 'password': 'password123'})
    assert created.status_code == 201
    for _ in range(settings.auth_rate_limit_max_attempts):
        response = client.post('/api/v1/auth/login', json={'username': 'limited-user', 'password': 'wrong-password'})
        assert response.status_code == 401
    limited = client.post('/api/v1/auth/login', json={'username': 'limited-user', 'password': 'wrong-password'})
    assert limited.status_code == 429


def test_password_is_hashed_and_access_token_uses_configured_claims(client: TestClient) -> None:
    password = 'password123'
    tokens = register_and_login(client, username='secure-user')
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == 'secure-user').one()
        assert user.password_hash != password
        assert user.password_hash.startswith('$2')
    finally:
        db.close()
    payload = decode_token(tokens['access_token'])
    assert payload['type'] == 'access'
    assert payload['iss'] == settings.jwt_issuer
    assert payload['aud'] == settings.jwt_audience
    assert payload['sub'] == str(payload['user_id'])
    expires_at = datetime.fromtimestamp(payload['exp'], tz=timezone.utc)
    max_expected_expiry = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes, seconds=5)
    assert expires_at <= max_expected_expiry


def test_booking_endpoints_require_authenticated_user(client: TestClient) -> None:
    start = datetime.now(timezone.utc) + timedelta(days=1)
    payload = {
        'room_id': 1,
        'title': 'Planning',
        'purpose': 'Sprint planning',
        'attendee_count': 3,
        'start_time': start.isoformat(),
        'end_time': (start + timedelta(hours=1)).isoformat(),
    }
    assert client.get('/api/v1/bookings/me').status_code == 401
    assert client.post('/api/v1/bookings', json=payload).status_code == 401
    assert client.delete('/api/v1/bookings/1').status_code == 401


def test_refresh_token_rotation_rejects_reuse(client: TestClient) -> None:
    tokens = register_and_login(client, username='refresh-user')
    refreshed = client.post('/api/v1/auth/refresh', json={'refresh_token': tokens['refresh_token']})
    assert refreshed.status_code == 200
    assert refreshed.json()['refresh_token'] != tokens['refresh_token']
    reused = client.post('/api/v1/auth/refresh', json={'refresh_token': tokens['refresh_token']})
    assert reused.status_code == 401


def test_logout_reads_access_token_from_header_and_revokes_one_session(client: TestClient) -> None:
    tokens = register_and_login(client, username='logout-user')
    response = client.post(
        '/api/v1/auth/logout',
        json={'refresh_token': tokens['refresh_token']},
        headers=auth_header(tokens),
    )
    assert response.status_code == 200

    db = SessionLocal()
    try:
        stored = db.scalar(select(RefreshToken))
        assert stored is not None
        assert stored.revoked is True
    finally:
        db.close()

    duplicated_access_token = client.post(
        '/api/v1/auth/logout',
        json={'access_token': tokens['access_token'], 'refresh_token': tokens['refresh_token']},
        headers=auth_header(tokens),
    )
    assert duplicated_access_token.status_code == 422


def test_logout_all_revokes_every_device_session(client: TestClient) -> None:
    first = register_and_login(client, username='multi-device-user')
    second_response = client.post(
        '/api/v1/auth/login',
        json={'username': 'multi-device-user', 'password': 'password123'},
        headers={'x-device-name': 'Phone'},
    )
    assert second_response.status_code == 200
    second = second_response.json()

    response = client.post('/api/v1/auth/logout-all', headers=auth_header(second))
    assert response.status_code == 200
    assert response.json()['revoked_sessions'] == 2

    db = SessionLocal()
    try:
        sessions = list(db.scalars(select(RefreshToken)).all())
        assert {item.token_hash for item in sessions} == {
            hash_refresh_token(first['refresh_token']),
            hash_refresh_token(second['refresh_token']),
        }
        assert all(item.revoked for item in sessions)
    finally:
        db.close()


def test_login_removes_expired_refresh_sessions(client: TestClient) -> None:
    tokens = register_and_login(client, username='cleanup-user')
    db = SessionLocal()
    try:
        expired = db.scalar(select(RefreshToken))
        assert expired is not None
        expired.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()
    finally:
        db.close()

    next_login = client.post('/api/v1/auth/login', json={'username': 'cleanup-user', 'password': 'password123'})
    assert next_login.status_code == 200

    db = SessionLocal()
    try:
        sessions = list(db.scalars(select(RefreshToken)).all())
        assert len(sessions) == 1
        assert sessions[0].token_hash != hash_refresh_token(tokens['refresh_token'])
    finally:
        db.close()


def test_periodic_cleanup_removes_expired_refresh_sessions(client: TestClient) -> None:
    register_and_login(client, username='scheduled-cleanup-user')
    db = SessionLocal()
    try:
        expired = db.scalar(select(RefreshToken))
        assert expired is not None
        expired.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()
    finally:
        db.close()

    assert cleanup_expired_refresh_tokens() == 1

    db = SessionLocal()
    try:
        assert db.scalar(select(RefreshToken)) is None
    finally:
        db.close()


def test_token_with_wrong_audience_is_rejected(client: TestClient) -> None:
    tokens = register_and_login(client, username='audience-user')
    payload = decode_token(tokens['access_token'])
    payload['aud'] = 'unexpected-audience'
    bad_token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    response = client.get('/api/v1/users/me', headers={'Authorization': f'Bearer {bad_token}'})
    assert response.status_code == 401


def test_room_creation_requires_admin_and_created_room_is_listed(client: TestClient) -> None:
    tokens = register_and_login(client)
    denied = client.post(
        '/api/v1/rooms',
        json={'name': 'Admin-Room', 'capacity': 8, 'location': 'HQ', 'description': None},
        headers=auth_header(tokens),
    )
    assert denied.status_code == 403
    promote_to_admin('alice')
    created = client.post(
        '/api/v1/rooms',
        json={'name': 'Admin-Room', 'capacity': 8, 'location': 'HQ', 'description': None},
        headers=auth_header(tokens),
    )
    assert created.status_code == 201
    assert created.json()['name'] == 'Admin-Room'
    listed = client.get('/api/v1/rooms')
    assert listed.status_code == 200
    assert any(room['name'] == 'Admin-Room' for room in listed.json())


def test_booking_conflict_and_cancel_flow(client: TestClient) -> None:
    tokens = register_and_login(client)
    promote_to_admin('alice')
    room = client.post(
        '/api/v1/rooms',
        json={'name': 'Focus-Room', 'capacity': 4, 'location': 'HQ', 'description': None},
        headers=auth_header(tokens),
    )
    assert room.status_code == 201
    start = datetime.now(timezone.utc) + timedelta(days=1)
    payload = {
        'room_id': room.json()['id'],
        'title': 'Planning',
        'purpose': 'Sprint planning',
        'attendee_count': 3,
        'start_time': start.isoformat(),
        'end_time': (start + timedelta(hours=1)).isoformat(),
    }
    first = client.post('/api/v1/bookings', json=payload, headers=auth_header(tokens))
    assert first.status_code == 201
    assert client.post('/api/v1/bookings', json=payload, headers=auth_header(tokens)).status_code == 409
    assert client.delete(f"/api/v1/bookings/{first.json()['id']}", headers=auth_header(tokens)).status_code == 200
    assert client.post('/api/v1/bookings', json=payload, headers=auth_header(tokens)).status_code == 201
