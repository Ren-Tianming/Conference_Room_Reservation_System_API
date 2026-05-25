from __future__ import annotations

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.models.user import User, UserRole


def register_and_login(client: TestClient, username: str) -> dict[str, str]:
    registered = client.post('/api/v1/auth/register', json={'username': username, 'password': 'password123'})
    assert registered.status_code == 201
    logged_in = client.post('/api/v1/auth/login', json={'username': username, 'password': 'password123'})
    assert logged_in.status_code == 200
    return logged_in.json()


def auth_header(tokens: dict[str, str]) -> dict[str, str]:
    return {'Authorization': f"Bearer {tokens['access_token']}"}


def promote_to_admin(username: str) -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).one()
        user.role = UserRole.ADMIN.value
        db.commit()
    finally:
        db.close()


def create_room(client: TestClient, tokens: dict[str, str], name: str = 'Concurrent-Room') -> int:
    created = client.post(
        '/api/v1/rooms',
        json={'name': name, 'capacity': 8, 'location': 'HQ', 'description': None},
        headers=auth_header(tokens),
    )
    assert created.status_code == 201
    return created.json()['id']
