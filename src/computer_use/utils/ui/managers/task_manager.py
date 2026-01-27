"""
Task lifecycle management for the dashboard.

This module owns task initialization and high-level dashboard start/stop
operations. Printing is delegated to the dashboard facade to keep this module
focused on state changes.
"""

from __future__ import annotations

import time
import uuid
from typing import Protocol

from rich.console import Console

from ..state import TaskState
from .shared_state import DashboardSharedState


class _TaskPrinter(Protocol):
    def _print_raw(self, content: str) -> None: ...

    def _flush(self) -> None: ...


class TaskManager:
    """Manage task lifecycle for the dashboard."""

    def __init__(
        self,
        console: Console,
        shared: DashboardSharedState,
        printer: _TaskPrinter,
    ) -> None:
        self._console = console
        self._shared = shared
        self._printer = printer

    def set_task(self, description: str) -> None:
        """Initialize a new task and fully reset prior UI state."""
        self._shared.is_running = False
        self._shared.task = TaskState(
            task_id=str(uuid.uuid4()),
            description=description,
            status="running",
        )
        self._shared.printed_agents.clear()
        self._shared.printed_tools.clear()
        self._shared.started_tools.clear()
        self._shared.nested_tools.clear()
        self._shared.last_thought_hash = None
        self._shared.header_printed = False
        self._shared.current_agent_name = None
        self._shared.pending_thought = None
        self._shared.pending_thought_agent_id = None
        self._shared.tool_history.clear()

    def start_dashboard(self) -> None:
        """Mark the dashboard as running and print the task header."""
        if self._shared.is_running or not self._shared.task:
            return
        self._shared.is_running = True
        self._print_task_header()

    def stop_dashboard(self) -> None:
        """Mark the dashboard as stopped."""
        self._shared.is_running = False

    def complete_task(self, success: bool = True) -> None:
        """Mark the current task as complete."""
        if not self._shared.task:
            return
        self._shared.task.status = "complete" if success else "error"
        self._shared.task.end_time = time.time()

    def _print_task_header(self) -> None:
        """Print the HUD-style task header."""
        if self._shared.header_printed or not self._shared.task:
            return
        self._shared.header_printed = True
        return
