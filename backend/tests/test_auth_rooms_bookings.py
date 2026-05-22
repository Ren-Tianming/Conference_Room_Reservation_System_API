from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import settings
from app.core.security import decode_token
from app.db.session import SessionLocal
from app.models.user import User, UserRole


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
    body = response.json()
    assert body['username'] == 'alice'
    assert body['role'] == UserRole.USER.value


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
    body = response.json()
    assert body['token_type'] == 'bearer'
    assert body['access_token']
    assert body['refresh_token']


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
    end = start + timedelta(hours=1)
    payload = {
        'room_id': 1,
        'title': 'Planning',
        'purpose': 'Sprint planning',
        'attendee_count': 3,
        'start_time': start.isoformat(),
        'end_time': end.isoformat(),
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
    room_id = room.json()['id']

    start = datetime.now(timezone.utc) + timedelta(days=1)
    end = start + timedelta(hours=1)
    payload = {
        'room_id': room_id,
        'title': 'Planning',
        'purpose': 'Sprint planning',
        'attendee_count': 3,
        'start_time': start.isoformat(),
        'end_time': end.isoformat(),
    }

    first = client.post('/api/v1/bookings', json=payload, headers=auth_header(tokens))
    assert first.status_code == 201

    conflict = client.post('/api/v1/bookings', json=payload, headers=auth_header(tokens))
    assert conflict.status_code == 409

    booking_id = first.json()['id']
    cancelled = client.delete(f'/api/v1/bookings/{booking_id}', headers=auth_header(tokens))
    assert cancelled.status_code == 200

    recreated = client.post('/api/v1/bookings', json=payload, headers=auth_header(tokens))
    assert recreated.status_code == 201
