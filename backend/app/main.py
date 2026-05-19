from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.session import create_db_and_tables
from app.services.admin_service import seed_bootstrap_admin
from app.services.room_service import seed_default_rooms


configure_logging(settings.debug)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.auto_create_tables:
        create_db_and_tables()
        seed_default_rooms()
        seed_bootstrap_admin()
    yield


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Conference Room Reservation System API is running."}
