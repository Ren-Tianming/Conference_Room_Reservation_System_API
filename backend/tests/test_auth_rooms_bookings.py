from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

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


def test_room_creation_requires_admin(client: TestClient) -> None:
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
