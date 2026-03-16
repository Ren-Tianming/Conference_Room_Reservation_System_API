from fastapi import APIRouter
from sqlalchemy import text

from app.db.redis_client import get_redis
from app.db.session import SessionLocal

router = APIRouter()


@router.get('/health')
def health_check() -> dict:
    return {'status': 'ok'}


@router.get('/ready')
def readiness_check() -> dict:
    db = SessionLocal()
    try:
        db.execute(text('SELECT 1'))
    finally:
        db.close()

    redis_client = get_redis()
    redis_client.ping()
    return {'status': 'ready'}
