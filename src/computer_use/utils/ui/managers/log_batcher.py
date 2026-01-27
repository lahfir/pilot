"""
Log batching utilities for UI output.

This module provides LogBatcher which coalesces frequent log entries into fewer
prints. The batching behavior is preserved from the previous monolithic
dashboard implementation.
"""

from __future__ import annotations

import threading
from typing import Optional, Protocol, cast

from ..state import ActionType


class _LogSink(Protocol):
    def add_log_entry(
        self,
        action_type: ActionType,
        message: str,
        target: Optional[str] = None,
        status: str = "pending",
    ) -> int: ...


class LogBatcher:
    """Batch log entries to reduce UI updates."""

    def __init__(
        self,
        batch_size: int = 10,
        timeout_sec: float = 0.2,
        sink: Optional[_LogSink] = None,
    ):
        self._sink = sink
        self._batch: list[tuple[ActionType, str, Optional[str], str]] = []
        self._lock = threading.Lock()
        self._timer: Optional[threading.Timer] = None
        self._batch_size = batch_size
        self._timeout_sec = timeout_sec

    def add(
        self,
        action_type: ActionType,
        message: str,
        target: Optional[str] = None,
        status: str = "pending",
    ) -> None:
        """Queue an entry and flush based on batch size or timeout."""
        with self._lock:
            self._batch.append((action_type, message, target, status))
            if len(self._batch) >= self._batch_size:
                self._flush_locked()
            elif self._timer is None:
                self._timer = threading.Timer(self._timeout_sec, self._flush)
                self._timer.start()

    def _flush(self) -> None:
        with self._lock:
            self._flush_locked()

    def _flush_locked(self) -> None:
        if not self._batch:
            return

        count = len(self._batch)
        action_type, message, target, status = self._batch[-1]

        if count > 1:
            message = f"{message} (+{count - 1} more)"

        sink = self._sink
        if sink is None:
            from ..dashboard import dashboard

            sink = cast(_LogSink, dashboard)

        sink.add_log_entry(action_type, message, target, status)
        self._batch.clear()

        if self._timer:
            self._timer.cancel()
            self._timer = None

    def flush_now(self) -> None:
        """Force flush any buffered entries immediately."""
        self._flush()
