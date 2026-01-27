"""
Thread-safety tests for TUI status refresh.
"""

from __future__ import annotations

import time

from rich.console import Console

from computer_use.utils.ui.managers.shared_state import DashboardSharedState
from computer_use.utils.ui.managers.status_manager import StatusManager
from computer_use.utils.ui.state import TaskState


class _DummyRenderer:
    def set_status(self, renderable) -> None:
        _ = renderable

    def stop_status(self) -> None:
        pass


def test_status_manager_stop_cancels_timer() -> None:
    """Verify stop cancels periodic refresh and does not reschedule."""
    console = Console(force_terminal=False, force_interactive=False, record=True)
    shared = DashboardSharedState()
    shared.is_running = True
    shared.task = TaskState(task_id="t", description="d", status="running")

    status = StatusManager(console, shared, _DummyRenderer())
    status.start()
    time.sleep(0.05)
    status.stop()
    time.sleep(0.2)

    assert status._status_timer is None
