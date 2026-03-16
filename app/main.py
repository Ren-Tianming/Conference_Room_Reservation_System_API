from fastapi import FastAPI

from app.api.routes import auth, bookings, health, rooms
from app.core.config import settings
from app.db.session import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    version='2.0.0',
    docs_url='/docs',
    redoc_url='/redoc',
)

app.include_router(health.router, prefix=settings.api_v1_prefix, tags=['health'])
app.include_router(auth.router, prefix=f"{settings.api_v1_prefix}/auth", tags=['auth'])
app.include_router(rooms.router, prefix=f"{settings.api_v1_prefix}/rooms", tags=['rooms'])
app.include_router(bookings.router, prefix=f"{settings.api_v1_prefix}/bookings", tags=['bookings'])
