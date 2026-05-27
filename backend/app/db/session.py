from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base

database_url = settings.sqlalchemy_database_url
if settings.sqlalchemy_database_url_string.startswith('sqlite'):
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        future=True,
        pool_pre_ping=True,
    )
else:
    engine = create_engine(
        database_url,
        future=True,
        pool_pre_ping=True,
        isolation_level='READ COMMITTED',
    )
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def create_db_and_tables() -> None:
    Base.metadata.create_all(bind=engine)
