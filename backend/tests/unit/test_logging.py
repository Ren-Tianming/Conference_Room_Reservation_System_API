from __future__ import annotations

import json
import logging

from app.core.logging import JsonFormatter, reset_request_id, set_request_id


def test_json_logging_includes_trace_and_audit_fields() -> None:
    token = set_request_id('request-trace-1')
    try:
        record = logging.LogRecord(
            name='app.audit',
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg='Booking created.',
            args=(),
            exc_info=None,
        )
        record.event = 'booking_created'
        record.user_id = 3
        record.booking_id = 7
        payload = json.loads(JsonFormatter().format(record))
    finally:
        reset_request_id(token)

    assert payload['level'] == 'INFO'
    assert payload['request_id'] == 'request-trace-1'
    assert payload['event'] == 'booking_created'
    assert payload['user_id'] == 3
    assert payload['booking_id'] == 7
