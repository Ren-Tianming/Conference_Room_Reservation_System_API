from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.routes import health as health_routes
from app.core.observability import reset_metrics
from app import main as app_main


class FailingDatabase:
    def execute(self, _statement: object) -> None:
        raise RuntimeError('database unavailable')

    def close(self) -> None:
        pass


def test_health(client: TestClient) -> None:
    response = client.get('/api/v1/health')

    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_request_id_header_and_metrics_endpoint(client: TestClient) -> None:
    reset_metrics()
    response = client.get('/api/v1/health', headers={'X-Request-ID': 'request-trace-1'})

    assert response.headers['X-Request-ID'] == 'request-trace-1'
    metrics = client.get('/api/v1/metrics')
    assert metrics.status_code == 200
    assert 'text/plain' in metrics.headers['content-type']
    assert 'http_requests_total{method="GET",path="/api/v1/health",status="200"} 1' in metrics.text
    assert 'http_request_duration_seconds_count{method="GET",path="/api/v1/health",status="200"} 1' in metrics.text


def test_invalid_request_id_is_replaced(client: TestClient) -> None:
    response = client.get('/api/v1/health', headers={'X-Request-ID': 'not allowed value'})

    assert response.status_code == 200
    assert response.headers['X-Request-ID'] != 'not allowed value'
    assert len(response.headers['X-Request-ID']) == 32


def test_startup_can_seed_admin_without_auto_creating_tables(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(app_main.settings, 'auto_create_tables', False)
    monkeypatch.setattr(app_main, 'seed_bootstrap_admin', lambda: calls.append('admin'))

    with TestClient(app_main.app):
        pass

    assert calls == ['admin']


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
