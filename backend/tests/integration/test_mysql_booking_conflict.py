from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Barrier

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text

from app.db.session import SessionLocal
from app.main import app
from app.models.booking import Booking, BookingStatus
from tests.integration.helpers import auth_header, create_room, promote_to_admin, register_and_login

pytestmark = pytest.mark.integration


def test_mysql_uses_read_committed_isolation(client: TestClient) -> None:
    db = SessionLocal()
    try:
        isolation_level = db.execute(text('SELECT @@transaction_isolation')).scalar_one()
        assert isolation_level.upper().replace('-', ' ') == 'READ COMMITTED'
    finally:
        db.close()


def test_concurrent_overlapping_bookings_allow_only_one_commit(client: TestClient) -> None:
    tokens = register_and_login(client, 'mysql-booking-user')
    promote_to_admin('mysql-booking-user')
    room_id = create_room(client, tokens)
    start = datetime.now(timezone.utc) + timedelta(days=1)
    payload = {
        'room_id': room_id,
        'title': 'Concurrent planning',
        'purpose': 'MySQL and Redis lock integration',
        'attendee_count': 4,
        'start_time': start.isoformat(),
        'end_time': (start + timedelta(hours=1)).isoformat(),
    }
    gate = Barrier(2)

    def submit_booking() -> int:
        gate.wait()
        with TestClient(app) as concurrent_client:
            response = concurrent_client.post('/api/v1/bookings', json=payload, headers=auth_header(tokens))
            return response.status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = sorted(executor.map(lambda _: submit_booking(), range(2)))

    assert statuses == [201, 409]
    db = SessionLocal()
    try:
        count = db.scalar(
            select(func.count(Booking.id)).where(
                Booking.room_id == room_id,
                Booking.status == BookingStatus.ACTIVE.value,
            )
        )
        assert count == 1
    finally:
        db.close()
