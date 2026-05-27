from __future__ import annotations

from typing import Union

from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import settings
from app.core.observability import render_prometheus_metrics
from app.core.redis_client import get_redis_client
from app.db.session import SessionLocal

router = APIRouter()


@router.get('/health')
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get('/metrics', include_in_schema=False)
def metrics() -> Response:
    return Response(
        content=render_prometheus_metrics(),
        media_type='text/plain; version=0.0.4',
    )


@router.get('/ready', response_model=None)
def ready() -> Union[dict[str, str], JSONResponse]:
    db_status = "ok"
    redis_status = "unavailable"

    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"
    finally:
        db.close()

    redis_client = get_redis_client()
    if redis_client is not None:
        try:
            redis_client.ping()
            redis_status = "ok"
        except Exception:
            redis_status = "error"

    components = {"database": db_status, "redis": redis_status}
    redis_required = settings.require_redis_for_locks or settings.require_redis_for_token_blacklist
    if db_status != "ok" or (redis_required and redis_status != "ok"):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", **components},
        )

    readiness_status = "ready" if redis_status == "ok" else "degraded"
    return {"status": readiness_status, **components}
