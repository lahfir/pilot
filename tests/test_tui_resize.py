"""
Tests for terminal resize handling.
"""

from __future__ import annotations

from computer_use.utils.ui.core import resize_handler as resize_module


def test_get_terminal_size_returns_tuple() -> None:
    """Verify terminal size helper returns a stable tuple."""
    cols, rows = resize_module.get_terminal_size()
    assert isinstance(cols, int)
    assert isinstance(rows, int)
    assert cols > 0
    assert rows > 0


def test_setup_resize_handler_installs_handler(monkeypatch) -> None:
    """Verify the resize handler attempts to register SIGWINCH when available."""
    calls = []

    def fake_signal(sig, handler):
        calls.append((sig, handler))

    monkeypatch.setattr(resize_module.signal, "signal", fake_signal)
    monkeypatch.setattr(resize_module.sys, "platform", "linux", raising=False)

    def cb(cols: int, rows: int) -> None:
        _ = cols, rows

    resize_module.setup_resize_handler(cb)
    assert calls
