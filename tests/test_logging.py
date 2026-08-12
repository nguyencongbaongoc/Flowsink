"""Tests for the centralized logging system."""

from __future__ import annotations

import io
import logging
from pathlib import Path

import pytest

from activity_engine.logging import (
    TRACE,
    configure_logging,
    get_log_context,
    get_logger,
    reset_log_context,
    sanitize_dict,
    sanitize_message,
    sanitize_url,
    set_log_context,
)
from activity_engine.logging.context import log_context
from activity_engine.logging.logger import StructuredFormatter
from activity_engine.logging.sanitize import _REDACTED


@pytest.fixture()
def reset_logger_state():
    """Reset the activity_engine logger and context between tests."""
    reset_log_context()
    logger = logging.getLogger("activity_engine")
    logger.handlers.clear()
    logger.setLevel(logging.NOTSET)
    logger.propagate = False
    yield
    reset_log_context()
    logger.handlers.clear()
    logger.setLevel(logging.NOTSET)


@pytest.fixture()
def log_buffer():
    """Capture all output from the activity_engine logger."""
    buffer = io.StringIO()
    handler = logging.StreamHandler(buffer)
    handler.setFormatter(StructuredFormatter(use_color=False))
    logger = logging.getLogger("activity_engine")
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(TRACE)
    logger.propagate = False
    return buffer

# ---------------------------------------------------------------------------
# Sanitization tests
# ---------------------------------------------------------------------------

class TestSanitizeMessage:
    def test_redacts_password(self):
        msg = "Login failed for user=admin password=hunter2"
        result = sanitize_message(msg)
        assert "hunter2" not in result
        assert _REDACTED in result

    def test_redacts_apikey(self):
        msg = "Request with api_key=abc123def456"
        result = sanitize_message(msg)
        assert "abc123def456" not in result
        assert _REDACTED in result

    def test_redacts_bearer_token(self):
        msg = "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0"
        result = sanitize_message(msg)
        assert "eyJhbGciOiJIUzI1NiJ9" not in result
        assert _REDACTED in result

    def test_redacts_access_token(self):
        msg = "access_token=12345"
        result = sanitize_message(msg)
        assert "12345" not in result

    def test_redacts_cookie(self):
        msg = "Set-Cookie: session=abc123; Path=/"
        result = sanitize_message(msg)
        assert "abc123" not in result

    def test_leaves_normal_text(self):
        msg = "User focused on Visual Studio Code"
        assert sanitize_message(msg) == msg

    def test_leaves_urls_intact(self):
        msg = "Navigated to https://classroom.google.com"
        assert "classroom.google.com" in sanitize_message(msg)

class TestSanitizeUrl:
    def test_strips_query_params(self):
        url = "https://example.com/login?password=secret&token=abc"
        result = sanitize_url(url)
        assert "secret" not in result
        assert "abc" not in result
        assert "https://example.com/login" in result

    def test_no_query_ignored(self):
        url = "https://example.com/page"
        assert sanitize_url(url) == url

class TestSanitizeDict:
    def test_redacts_sensitive_keys(self):
        data = {
            "username": "student1",
            "password": "hunter2",
            "api_key": "abc123",
            "nested": {"access_token": "tok123", "name": "safe"},
        }
        result = sanitize_dict(data)
        assert result["username"] == "student1"
        assert result["password"] == _REDACTED
        assert result["api_key"] == _REDACTED
        assert result["nested"]["access_token"] == _REDACTED
        assert result["nested"]["name"] == "safe"

    def test_none_passthrough(self):
        assert sanitize_dict(None) is None

# ---------------------------------------------------------------------------
# TRACE level tests
# ---------------------------------------------------------------------------

class TestTraceLevel:
    def test_trace_constant(self):
        assert TRACE == 5

    def test_trace_registered(self):
        assert logging.getLevelName(TRACE) == "TRACE"

    def test_trace_logging(self, reset_logger_state, log_buffer):
        logger = get_logger("activity_engine.test_trace", component="TEST")
        logger.trace("Trace message", event="TRACE_EVENT")
        output = log_buffer.getvalue()
        assert "[TRACE]" in output
        assert "Trace message" in output
        assert "[TEST]" in output
        assert "[TRACE_EVENT]" in output

# ---------------------------------------------------------------------------
# Formatting tests
# ---------------------------------------------------------------------------

class TestStructuredFormat:
    def test_log_format(self, reset_logger_state, log_buffer):
        logger = get_logger("activity_engine.test_format", component="SCREEN")
        logger.info("Monitor detected", event="DETECTED", monitor=1, width=1920)
        output = log_buffer.getvalue()
        assert "[INFO]" in output
        assert "[SCREEN]" in output
        assert "[DETECTED]" in output
        assert "Monitor detected" in output
        assert "monitor=1" in output
        assert "width=1920" in output

    def test_timestamp_format(self, reset_logger_state, log_buffer):
        import re
        logger = get_logger("activity_engine.test_ts")
        logger.info("hello")
        output = log_buffer.getvalue()
        assert re.match(r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]", output)

    def test_default_component(self, reset_logger_state, log_buffer):
        logger = get_logger("activity_engine.test_default")
        logger.info("hello")
        assert "[SYSTEM]" in log_buffer.getvalue()

    def test_exception_included(self, reset_logger_state, log_buffer):
        logger = get_logger("activity_engine.test_exc")
        try:
            raise ValueError("boom")
        except ValueError:
            logger.exception("Operation failed", event="ERROR")
        output = log_buffer.getvalue()
        assert "ValueError: boom" in output
        assert "Operation failed" in output

# ---------------------------------------------------------------------------
# Correlation context tests
# ---------------------------------------------------------------------------

class TestLogContext:
    def test_set_and_get(self, reset_logger_state):
        set_log_context(event_id="evt-1", session_id="sess-1", device_id="dev-1")
        ctx = get_log_context()
        assert ctx["event_id"] == "evt-1"
        assert ctx["session_id"] == "sess-1"
        assert ctx["device_id"] == "dev-1"

    def test_reset(self, reset_logger_state):
        set_log_context(event_id="evt-1")
        reset_log_context()
        assert get_log_context() == {}

    def test_context_logged(self, reset_logger_state, log_buffer):
        logger = get_logger("activity_engine.test_ctx")
        set_log_context(event_id="evt-123", session_id="sess-456")
        logger.info("Event processed", event="PROCESSED")
        output = log_buffer.getvalue()
        assert "event_id=evt-123" in output
        assert "session_id=sess-456" in output

    def test_context_manager(self, reset_logger_state, log_buffer):
        logger = get_logger("activity_engine.test_ctx_mgr")
        with log_context(event_id="evt-inner", session_id="sess-inner"):
            logger.info("Inside context", event="INNER")
        logger.info("Outside context", event="OUTER")
        output = log_buffer.getvalue()
        lines = output.strip().splitlines()
        assert "event_id=evt-inner" in lines[0]
        assert "event_id=evt-inner" not in lines[1]

    def test_context_isolation_between_sync_contexts(self, reset_logger_state):
        """ContextVars should not leak between threads."""
        import threading

        results: dict[str, dict] = {}

        def worker(name: str, event_id: str) -> None:
            set_log_context(event_id=event_id)
            results[name] = get_log_context()

        t1 = threading.Thread(target=worker, args=("t1", "evt-1"))
        t2 = threading.Thread(target=worker, args=("t2", "evt-2"))
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        assert results["t1"]["event_id"] == "evt-1"
        assert results["t2"]["event_id"] == "evt-2"

# ---------------------------------------------------------------------------
# log_error helper tests
# ---------------------------------------------------------------------------

class TestLogError:
    def test_log_error_structured(self, reset_logger_state, log_buffer):
        from activity_engine.logging import log_error

        logger = get_logger("activity_engine.test_log_error")
        try:
            raise RuntimeError("backend unavailable")
        except RuntimeError as exc:
            log_error(logger, "fetch_events", exc, component="ADAPTER", event="ERROR")
        output = log_buffer.getvalue()
        assert "ERROR" in output
        assert "fetch_events" in output
        assert "RuntimeError" in output
        assert "backend unavailable" in output

# ---------------------------------------------------------------------------
# configure_logging tests
# ---------------------------------------------------------------------------

class TestConfigureLogging:
    def test_configure_logging_sets_level(self, reset_logger_state):
        import activity_engine.logging.logger as logger_module
        logger_module._LOG_CONFIGURED = False

        configure_logging(level="DEBUG", console=False, file_logging=False)
        root = logging.getLogger("activity_engine")
        assert root.level == logging.DEBUG

    def test_setup_logging_files(self, reset_logger_state, tmp_path):
        import activity_engine.logging.logger as logger_module
        logger_module._LOG_CONFIGURED = False

        configure_logging(
            level="INFO",
            console=False,
            file_logging=True,
            log_dir=tmp_path,
        )
        assert (tmp_path / "flowsink.log").exists()
        assert (tmp_path / "flowsink-error.log").exists()
        assert (tmp_path / "flowsink-debug.log").exists()

# ---------------------------------------------------------------------------
# utils.logging backward compatibility
# ---------------------------------------------------------------------------

class TestBackwardCompatibleUtils:
    def test_create_logger_exists(self):
        from activity_engine.utils.logging import create_logger
        logger = create_logger("test_compat")
        assert logger.name == "test_compat"

    def test_reexports(self):
        from activity_engine.utils.logging import (
            TRACE as _TRACE,
            get_log_context as _glc,
            sanitize_message as _sm,
        )
        assert _TRACE == TRACE
        assert _glc is get_log_context
        assert _sm is sanitize_message
