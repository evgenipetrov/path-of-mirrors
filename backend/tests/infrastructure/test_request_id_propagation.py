"""Tests for request_id propagation through structured logging.

This test suite verifies that the RequestLoggingMiddleware correctly:
1. Generates a unique request_id for each request
2. Binds the request_id to structlog context
3. Propagates the request_id through all log messages in the request lifecycle
4. Returns the request_id in the X-Request-ID response header
"""

import json
import logging
import re
from io import StringIO

import pytest
import structlog
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def capture_logs(monkeypatch):
    """Capture structlog JSON output for verification.

    This fixture:
    1. Reconfigures structlog to write JSON to a StringIO buffer
    2. Gets a fresh logger instance that uses the new configuration
    3. Patches the middleware module's logger with the fresh instance
    4. Yields the StringIO buffer for test assertions
    5. Restores the original logging configuration
    """
    output = StringIO()

    # Configure structlog to write JSON to our StringIO
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=output),
        cache_logger_on_first_use=False,
    )

    # Get a fresh logger instance that uses the new configuration
    # This is critical: we must create a new logger AFTER reconfiguring
    fresh_logger = structlog.get_logger("src.infrastructure.middleware")

    # Patch the middleware module's cached logger
    import src.infrastructure.middleware

    monkeypatch.setattr(src.infrastructure.middleware, "logger", fresh_logger)

    yield output

    # Restore default configuration
    from src.infrastructure.logging import setup_logging

    setup_logging()


def test_request_id_in_response_header(client):
    """Test that X-Request-ID header is present in response."""
    response = client.get("/health")

    # Verify X-Request-ID header exists
    assert "X-Request-ID" in response.headers

    # Verify it's a valid UUID
    request_id = response.headers["X-Request-ID"]
    uuid_pattern = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
    assert uuid_pattern.match(request_id), f"Invalid UUID format: {request_id}"


def test_unique_request_ids_for_different_requests(client):
    """Test that different requests get different request_ids."""
    response1 = client.get("/health")
    response2 = client.get("/health")

    request_id_1 = response1.headers["X-Request-ID"]
    request_id_2 = response2.headers["X-Request-ID"]

    # Verify they are different
    assert request_id_1 != request_id_2


def test_request_id_propagates_through_logs(client, capture_logs):
    """Test that request_id appears in all log messages during request processing."""
    # Make a request
    response = client.get("/health")
    request_id = response.headers["X-Request-ID"]

    # Parse JSON logs
    log_output = capture_logs.getvalue()
    log_lines = [line for line in log_output.strip().split("\n") if line]

    # Verify we have logs
    assert len(log_lines) >= 2, (
        f"Expected at least request_started and request_completed logs, "
        f"got {len(log_lines)} lines. Output: {log_output}"
    )

    # Parse all JSON log entries
    logs = []
    for line in log_lines:
        try:
            logs.append(json.loads(line))
        except json.JSONDecodeError as e:
            pytest.fail(f"Failed to parse JSON log line: {line!r}. Error: {e}")

    # Verify all logs contain the same request_id
    for log in logs:
        assert "request_id" in log, f"Log entry missing request_id: {log}"
        assert log["request_id"] == request_id, (
            f"Log request_id {log['request_id']} doesn't match header {request_id}"
        )

    # Verify we have the expected log events
    events = [log.get("event") for log in logs]
    assert "request_started" in events, f"Missing request_started event. Events: {events}"
    assert "request_completed" in events, f"Missing request_completed event. Events: {events}"


def test_request_id_bound_to_logger_context(client, capture_logs):
    """Test that request_id is bound to structlog context during request."""
    response = client.get("/health")
    request_id = response.headers["X-Request-ID"]

    # Parse logs to verify context binding
    log_output = capture_logs.getvalue()
    log_lines = [line for line in log_output.strip().split("\n") if line]

    # All logs should have the request_id from context
    for line in log_lines:
        try:
            log = json.loads(line)
            if "event" in log:  # Skip non-event logs
                assert log.get("request_id") == request_id
                assert "method" in log  # Also bound by middleware
                assert "path" in log  # Also bound by middleware
        except json.JSONDecodeError:
            pytest.fail(f"Failed to parse JSON log line: {line!r}")


def test_request_id_clears_between_requests(client, capture_logs):
    """Test that request_id context is cleared between requests.

    This verifies that contextvars.clear_contextvars() is called,
    preventing request_id leakage between requests.
    """
    # Make two requests
    response1 = client.get("/health")
    response2 = client.get("/health")

    # Get their request_ids
    request_id_1 = response1.headers["X-Request-ID"]
    request_id_2 = response2.headers["X-Request-ID"]

    # Verify they are different (context was cleared)
    assert request_id_1 != request_id_2

    # Parse logs and verify no cross-contamination
    log_output = capture_logs.getvalue()
    log_lines = [line for line in log_output.strip().split("\n") if line]

    # Collect all request_ids from logs
    log_request_ids = set()
    for line in log_lines:
        try:
            log = json.loads(line)
            if "request_id" in log:
                log_request_ids.add(log["request_id"])
        except json.JSONDecodeError:
            pytest.fail(f"Failed to parse JSON log line: {line!r}")

    # Verify we have exactly two distinct request_ids in logs
    assert len(log_request_ids) == 2, (
        f"Expected exactly 2 unique request_ids in logs, got {len(log_request_ids)}. "
        f"Request IDs: {log_request_ids}"
    )
    assert request_id_1 in log_request_ids
    assert request_id_2 in log_request_ids


def test_request_id_format_consistency(client):
    """Test that request_id format is consistent across requests."""
    uuid_pattern = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

    # Test multiple requests
    for _ in range(5):
        response = client.get("/health")
        request_id = response.headers["X-Request-ID"]
        assert uuid_pattern.match(request_id), f"Invalid UUID format: {request_id}"


def test_request_id_propagation_documentation():
    """Document how request_id propagation works.

    This is a documentation test that explains the flow:

    1. Request arrives at RequestLoggingMiddleware
    2. Middleware generates UUID via uuid4()
    3. Middleware binds request_id to structlog context via:
       structlog.contextvars.bind_contextvars(request_id=request_id, ...)
    4. All subsequent log calls within this request automatically include request_id
    5. Middleware adds X-Request-ID header to response
    6. Context is cleared at start of next request

    This ensures:
    - Request tracing across distributed logs
    - No manual request_id passing required
    - Automatic propagation to all service calls

    The above tests verify:
    - test_request_id_in_response_header: Header presence and UUID format
    - test_unique_request_ids_for_different_requests: UUID uniqueness
    - test_request_id_propagates_through_logs: Actual log propagation (REAL TEST)
    - test_request_id_bound_to_logger_context: Context binding verification
    - test_request_id_clears_between_requests: No leakage between requests
    - test_request_id_format_consistency: UUID format consistency
    """
    # This test always passes - it's for documentation
    assert True
