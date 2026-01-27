"""
Tests for terminal UI rendering utilities.
"""

from __future__ import annotations

from unittest.mock import patch

from hypothesis import given, strategies as st

from computer_use.utils.ui.core import responsive as responsive_module
from computer_use.utils.ui.core.responsive import ResponsiveWidth


@given(st.text(max_size=2000))
def test_truncate_never_exceeds_target_width(text: str) -> None:
    """Verify responsive truncation respects computed width."""

    def _fixed_size(fallback=(80, 24)):
        _ = fallback
        return (80, 24)

    with patch.object(responsive_module, "get_terminal_size", _fixed_size):
        truncated = ResponsiveWidth.truncate(text, max_ratio=0.5, min_width=10)
        assert len(truncated) <= 40
