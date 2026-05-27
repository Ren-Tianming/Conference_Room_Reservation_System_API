from __future__ import annotations

import asyncio
import logging
import re
import time
import uuid
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.logging import configure_logging, reset_request_id, set_request_id
from app.core.observability import record_request
from app.db.session import create_db_and_tables
from app.services.admin_service import seed_bootstrap_admin
from app.services.auth_service import cleanup_expired_refresh_tokens
from app.services.room_service import seed_default_rooms


configure_logging(settings.debug, settings.log_level)
request_logger = logging.getLogger('app.request')
REQUEST_ID_PATTERN = re.compile(r'^[A-Za-z0-9._:-]{1,128}$')


async def remove_expired_refresh_tokens_periodically() -> None:
    while True:
        await asyncio.sleep(settings.refresh_token_cleanup_interval_seconds)
        await asyncio.to_thread(cleanup_expired_refresh_tokens)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.auto_create_tables:
        create_db_and_tables()
        seed_default_rooms()
    seed_bootstrap_admin()
    cleanup_task = asyncio.create_task(remove_expired_refresh_tokens_periodically())
    try:
        yield
    finally:
        cleanup_task.cancel()
        with suppress(asyncio.CancelledError):
            await cleanup_task


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, unhandled_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware('http')
async def observe_request(request: Request, call_next):
    provided_request_id = request.headers.get('X-Request-ID', '').strip()
    request_id = provided_request_id if REQUEST_ID_PATTERN.fullmatch(provided_request_id) else uuid.uuid4().hex
    token = set_request_id(request_id)
    started_at = time.perf_counter()
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers['X-Request-ID'] = request_id
        return response
    finally:
        duration_seconds = time.perf_counter() - started_at
        route = request.scope.get('route')
        path = getattr(route, 'path', request.url.path)
        record_request(
            method=request.method,
            path=path,
            status_code=status_code,
            duration_seconds=duration_seconds,
        )
        request_logger.info(
            'HTTP request completed.',
            extra={
                'event': 'http_request_completed',
                'method': request.method,
                'path': path,
                'status_code': status_code,
                'duration_ms': round(duration_seconds * 1000, 3),
            },
        )
        reset_request_id(token)


app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Conference Room Reservation System API is running."}
