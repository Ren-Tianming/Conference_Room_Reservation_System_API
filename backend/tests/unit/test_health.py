from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.routes import health as health_routes


class FailingDatabase:
    def execute(self, _statement: object) -> None:
        raise RuntimeError('database unavailable')

    def close(self) -> None:
        pass


def test_health(client: TestClient) -> None:
    response = client.get('/api/v1/health')

    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_ready_returns_503_when_database_is_unavailable(
    client: TestClient,
    monkeypatch,
) -> None:
    monkeypatch.setattr(health_routes, 'SessionLocal', FailingDatabase)
    monkeypatch.setattr(health_routes, 'get_redis_client', lambda: None)

    response = client.get('/api/v1/ready')

    assert response.status_code == 503
    assert response.json() == {'status': 'not_ready', 'database': 'error', 'redis': 'unavailable'}


def test_ready_reports_degraded_when_optional_redis_is_unavailable(
    client: TestClient,
    monkeypatch,
) -> None:
    monkeypatch.setattr(health_routes, 'get_redis_client', lambda: None)

    response = client.get('/api/v1/ready')

    assert response.status_code == 200
    assert response.json() == {'status': 'degraded', 'database': 'ok', 'redis': 'unavailable'}
