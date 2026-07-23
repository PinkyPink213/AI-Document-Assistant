import json
import logging

from app.core.observability import (
    JsonFormatter,
    bind_request_context,
    reset_request_context,
)


def test_json_logs_include_request_and_conversation_context():
    tokens = bind_request_context("request-123", 42)
    try:
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="Request completed",
            args=(),
            exc_info=None,
        )
        record.event = "test.completed"
        payload = json.loads(JsonFormatter().format(record))
    finally:
        reset_request_context(tokens)

    assert payload["request_id"] == "request-123"
    assert payload["conversation_id"] == "42"
    assert payload["event"] == "test.completed"
