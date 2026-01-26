"""
Terminal resize handling utilities.

This module installs a SIGWINCH handler where available and provides helpers for
querying the current terminal size.
"""

from __future__ import annotations

import os
import signal
import sys
from typing import Callable, Optional, Tuple


_resize_callback: Optional[Callable[[int, int], None]] = None


def setup_resize_handler(callback: Callable[[int, int], None]) -> None:
    """
    Install a resize handler that calls the provided callback.

    Args:
        callback: Called with (columns, lines) when the terminal is resized
    """
    global _resize_callback
    _resize_callback = callback

    if sys.platform == "win32":
        return
    if not hasattr(signal, "SIGWINCH"):
        return

    previous = signal.getsignal(signal.SIGWINCH)

    def handler(signum: int, frame: object) -> None:
        _ = signum, frame
        if callable(previous):
            try:
                previous(signum, frame)
            except Exception:
                pass

        try:
            cols, rows = get_terminal_size()
        except Exception:
            return
        cb = _resize_callback
        if cb is not None:
            cb(cols, rows)

    signal.signal(signal.SIGWINCH, handler)


def get_terminal_size(fallback: Tuple[int, int] = (80, 24)) -> Tuple[int, int]:
    """
    Get the current terminal size.

    Args:
        fallback: Returned if the terminal size cannot be determined

    Returns:
        Tuple of (columns, rows)
    """
    try:
        size = os.get_terminal_size()
        return (size.columns, size.lines)
    except OSError:
        return fallback
