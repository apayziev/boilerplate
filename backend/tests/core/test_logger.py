import json
import logging
from io import StringIO

from app.core.logger import JsonFormatter, setup_logging


def test_setup_logging_replaces_root_handlers():
    setup_logging()
    root = logging.getLogger()
    assert len(root.handlers) == 1
    handler = root.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    assert isinstance(handler.formatter, JsonFormatter)


def test_json_formatter_emits_valid_json_with_extras():
    buf = StringIO()
    handler = logging.StreamHandler(buf)
    handler.setFormatter(JsonFormatter())

    logger = logging.getLogger("test_json_formatter")
    logger.handlers = [handler]
    logger.propagate = False
    logger.setLevel(logging.INFO)

    logger.info("request", extra={"request_id": "abc123", "method": "GET", "path": "/x", "status_code": 200})

    payload = json.loads(buf.getvalue().strip())
    assert payload["level"] == "INFO"
    assert payload["logger"] == "test_json_formatter"
    assert payload["message"] == "request"
    assert payload["request_id"] == "abc123"
    assert payload["method"] == "GET"
    assert payload["status_code"] == 200
    assert "timestamp" in payload
