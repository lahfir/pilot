"""
Responsive helpers for terminal UI.

This module centralizes width-dependent logic to reduce hardcoded widths and to
support terminal resizing more gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass

from .resize_handler import get_terminal_size


@dataclass(frozen=True)
class ResponsiveWidth:
    """Width helpers derived from the active terminal size."""

    @staticmethod
    def get_width() -> int:
        """Return the current terminal width in columns."""
        cols, _ = get_terminal_size()
        return cols

    @staticmethod
    def get_content_width(padding: int = 8, min_width: int = 40) -> int:
        """Return a safe content width for wrapped text."""
        return max(ResponsiveWidth.get_width() - padding, min_width)

    @staticmethod
    def truncate(text: str, max_ratio: float = 0.8, min_width: int = 40) -> str:
        """
        Truncate text based on terminal width.

        Args:
            text: Text to truncate
            max_ratio: Maximum ratio of terminal width to use
            min_width: Minimum width

        Returns:
            Possibly truncated text
        """
        width = max(int(ResponsiveWidth.get_width() * max_ratio), min_width)
        if len(text) <= width:
            return text
        if width <= 3:
            return text[:width]
        return text[: width - 3] + "..."
