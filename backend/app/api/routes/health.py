from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.core.redis_client import get_redis_client
from app.db.session import SessionLocal

router = APIRouter()


@router.get('/health')
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get('/ready')
def ready() -> dict[str, str]:
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

    return {"database": db_status, "redis": redis_status}
