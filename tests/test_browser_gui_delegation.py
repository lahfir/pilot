"""Tests for Browser-Use GUI delegation tool wiring."""

import pytest


def test_load_browser_tools_includes_delegate_to_gui_when_delegate_provided():
    """Ensure the delegation tool is registered when gui_delegate is provided."""
    pytest.importorskip("browser_use")

    class _StubGuiDelegate:
        def run_os_dialog_task(self, task: str):
            class _Result:
                success = True
                output = f"ok: {task}"

            return _Result()

    from computer_use.tools.browser import load_browser_tools

    tools, _, _ = load_browser_tools(gui_delegate=_StubGuiDelegate())

    assert tools is not None
    actions = tools.registry.registry.actions
    assert "delegate_to_gui" in actions
