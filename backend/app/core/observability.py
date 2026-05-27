from __future__ import annotations

from collections import defaultdict
from threading import Lock

_lock = Lock()
_request_counts: defaultdict[tuple[str, str, int], int] = defaultdict(int)
_request_duration_seconds: defaultdict[tuple[str, str, int], float] = defaultdict(float)


def record_request(*, method: str, path: str, status_code: int, duration_seconds: float) -> None:
    key = (method, path, status_code)
    with _lock:
        _request_counts[key] += 1
        _request_duration_seconds[key] += duration_seconds


def reset_metrics() -> None:
    with _lock:
        _request_counts.clear()
        _request_duration_seconds.clear()


def _escape_label(value: str) -> str:
    return value.replace('\\', '\\\\').replace('\n', '\\n').replace('"', '\\"')


def render_prometheus_metrics() -> str:
    lines = [
        '# HELP http_requests_total Total HTTP requests handled by the application.',
        '# TYPE http_requests_total counter',
    ]
    with _lock:
        request_counts = dict(_request_counts)
        durations = dict(_request_duration_seconds)

    for (method, path, status_code), count in sorted(request_counts.items()):
        labels = f'method="{_escape_label(method)}",path="{_escape_label(path)}",status="{status_code}"'
        lines.append(f'http_requests_total{{{labels}}} {count}')

    lines.extend(
        [
            '# HELP http_request_duration_seconds Time spent handling HTTP requests.',
            '# TYPE http_request_duration_seconds summary',
        ]
    )
    for (method, path, status_code), total in sorted(durations.items()):
        labels = f'method="{_escape_label(method)}",path="{_escape_label(path)}",status="{status_code}"'
        lines.append(f'http_request_duration_seconds_sum{{{labels}}} {total:.6f}')
        lines.append(f'http_request_duration_seconds_count{{{labels}}} {request_counts[(method, path, status_code)]}')

    return '\n'.join(lines) + '\n'
