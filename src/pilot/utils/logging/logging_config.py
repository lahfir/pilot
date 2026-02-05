"""
Centralized logging configuration for suppressing verbose third-party logs.
"""

import json
import logging
import os
import time
import warnings
from pathlib import Path
from typing import Any, Dict


NOISY_LIBRARIES = [
    "easyocr",
    "paddleocr",
    "werkzeug",
    "flask",
    "urllib3",
    "httpx",
    "httpcore",
    "google",
    "google.genai",
    "google.auth",
    "google.api_core",
    "google.generativeai",
    "langchain_google_genai",
    "litellm",
    "crewai",
    "grpc",
    "openai",
    "openai._base_client",
    "root",
]

BROWSER_LOGGERS = [
    "browser_use",
    "browser_use.agent",
    "browser_use.browser",
    "browser_use.tools",
    "browser_use.service",
    "browser_use.controller",
    "BrowserSession",
    "Agent",
]


class NullHandler(logging.Handler):
    """Handler that discards all log records."""

    def emit(self, record):
        pass


class GoogleApiKeyFilter(logging.Filter):
    """Filter to suppress Google API key duplicate warnings."""

    def filter(self, record):
        message = record.getMessage()
        if "Both GOOGLE_API_KEY and GEMINI_API_KEY" in message:
            return False
        if "Using GOOGLE_API_KEY" in message:
            return False
        return True


def _patch_crewai_printer() -> None:
    """
    Patch CrewAI's Printer class to suppress noisy debug messages.
    """
    try:
        from crewai.utilities.printer import Printer

        original_print = Printer.print

        @staticmethod
        def patched_print(
            content,
            color=None,
            sep=" ",
            end="\n",
            file=None,
            flush=False,
        ) -> None:
            if isinstance(content, str):
                if "Repaired JSON" in content:
                    return
            original_print(content, color, sep, end, file, flush)

        Printer.print = patched_print
    except ImportError:
        pass


def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging levels to suppress verbose output from third-party libraries.
    Sets up environment variables and configures all noisy loggers.

    Args:
        verbose: If True, allow browser-use logs to print. If False, silence them.
    """
    _patch_crewai_printer()
    warnings.filterwarnings("ignore")
    # Suppress Google API key duplicate warnings specifically
    warnings.filterwarnings(
        "ignore",
        message=".*Both GOOGLE_API_KEY and GEMINI_API_KEY.*",
        category=UserWarning,
    )
    warnings.filterwarnings(
        "ignore",
        message=".*Using GOOGLE_API_KEY.*",
        category=UserWarning,
    )

    os.environ["GRPC_VERBOSITY"] = "ERROR"
    os.environ["GLOG_minloglevel"] = "2"
    os.environ["PPOCR_SHOW_LOG"] = "False"
    os.environ["BROWSER_USE_LOGGING_LEVEL"] = "CRITICAL" if not verbose else "INFO"

    api_key_filter = GoogleApiKeyFilter()

    for logger_name in NOISY_LIBRARIES:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.CRITICAL)
        logger.propagate = False
        logger.handlers = [NullHandler()]
        logger.addFilter(api_key_filter)

    root_logger = logging.getLogger()
    root_logger.addFilter(api_key_filter)
    if not verbose:
        root_logger.setLevel(logging.WARNING)

    browser_level = logging.INFO if verbose else logging.CRITICAL

    for logger_name in BROWSER_LOGGERS:
        logger = logging.getLogger(logger_name)
        logger.setLevel(browser_level)
        logger.propagate = False
        logger.handlers = [NullHandler()] if not verbose else []

    werkzeug = logging.getLogger("werkzeug")
    werkzeug.disabled = True


def silence_flask_logs() -> None:
    """
    Silence Flask and Werkzeug logs for background servers.
    Call this before starting Flask apps.
    """
    log = logging.getLogger("werkzeug")
    log.setLevel(logging.CRITICAL)
    log.disabled = True

    flask_log = logging.getLogger("flask")
    flask_log.setLevel(logging.CRITICAL)
    flask_log.disabled = True


def silence_browser_logs() -> None:
    """
    Completely silence browser-use library logs.
    Call this after browser-use is imported to override its handlers.
    """
    for logger_name in BROWSER_LOGGERS:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.CRITICAL)
        logger.propagate = False
        logger.handlers = [NullHandler()]


_DEBUG_LOG_PATH = Path(__file__).parent.parent.parent / ".cursor" / "debug.log"
_DEBUG_SESSION_ID = "debug-session"
_DEBUG_RUN_ID = "run1"
_DEBUG_LLM_EVENT_LIMIT = 30
_debug_llm_events_logged = 0


def debug_log(
    hypothesis_id: str, location: str, message: str, data: Dict[str, Any]
) -> None:
    """
    Write a single NDJSON debug log line for runtime diagnosis.

    Args:
        hypothesis_id: Hypothesis identifier for grouping related logs
        location: Code location (file:function)
        message: Log message
        data: Additional data dictionary to include
    """
    global _debug_llm_events_logged
    payload = {
        "sessionId": _DEBUG_SESSION_ID,
        "runId": _DEBUG_RUN_ID,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    try:
        with open(_DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        return


def get_debug_llm_event_limit() -> int:
    """Get the limit for LLM event logging."""
    return _DEBUG_LLM_EVENT_LIMIT


def increment_debug_llm_events_logged() -> int:
    """Increment and return the count of logged LLM events."""
    global _debug_llm_events_logged
    _debug_llm_events_logged += 1
    return _debug_llm_events_logged
