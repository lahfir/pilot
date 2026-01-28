"""
Status manager for the dashboard.

This module owns the live status spinner and timer-based refresh. The initial
refactor preserves current behavior; later steps switch the backing renderer to
Rich Live + Layout while keeping this interface stable.
"""

from __future__ import annotations

import threading
import time
from typing import Optional

from rich.console import Console
from rich.text import Text

from ..core import RenderManager
from ..state import TaskState
from ..theme import HEADSET_BLINK_FRAMES, THEME
from .shared_state import DashboardSharedState


class StatusManager:
    """Manage the animated status display and periodic refresh."""

    def __init__(
        self, console: Console, shared: DashboardSharedState, renderer: RenderManager
    ) -> None:
        self._console = console
        self._shared = shared
        self._renderer = renderer

        self._status_timer: Optional[threading.Timer] = None
        self._status_lock = threading.Lock()
        self._current_status_message: str = ""
        self._active: bool = False

    def pause(self) -> None:
        """Stop any active spinner before printing other content."""
        return

    def start(self) -> None:
        """Start live status updates if the dashboard is running."""
        with self._status_lock:
            self._active = True
        self.show("Initializing...")

    def stop(self) -> None:
        """Stop live status updates and clear any active spinner."""
        with self._status_lock:
            self._active = False
            self._current_status_message = ""
            timer = self._status_timer
            self._status_timer = None
        if timer:
            try:
                timer.cancel()
            except Exception:
                pass
        self._renderer.stop_status()

    def show(self, message: str = "") -> None:
        """Show or update the animated status spinner."""
        if not self._shared.is_running or not self._shared.task:
            return

        should_schedule = False
        with self._status_lock:
            if not self._active:
                self._active = True
            self._current_status_message = message
            status_text = self._build_status_line(message)
            should_schedule = self._status_timer is None

        self._renderer.set_status(Text.from_markup(status_text))
        if should_schedule:
            self._schedule_next_refresh()

    def _get_refresh_interval(self, task: TaskState) -> float:
        if task.current_phase in ("thinking", "executing"):
            return 0.25
        return 1.0

    def _schedule_next_refresh(self) -> None:
        if not self._shared.task:
            return
        interval = self._get_refresh_interval(self._shared.task)

        def refresh() -> None:
            acquired = self._status_lock.acquire(blocking=False)
            if not acquired:
                self._status_timer = None
                self._schedule_next_refresh()
                return
            try:
                if (
                    not self._active
                    or not self._shared.is_running
                    or not self._shared.task
                ):
                    self._status_timer = None
                    return
                status_text = self._build_status_line()
                self._status_timer = None
            finally:
                self._status_lock.release()

            self._renderer.set_status(Text.from_markup(status_text))
            self._schedule_next_refresh()

        self._status_timer = threading.Timer(interval, refresh)
        self._status_timer.daemon = True
        self._status_timer.start()

    def _build_status_line(self, message: str = "") -> str:
        """
        Build the status line shown inside the spinner.

        This method preserves the existing HUD-style status format.
        """
        if not self._shared.task:
            return ""

        task = self._shared.task

        elapsed = time.time() - task.start_time
        if elapsed < 60:
            time_str = f"{int(elapsed)}s"
        else:
            time_str = f"{int(elapsed // 60)}m{int(elapsed % 60):02d}s"

        tokens_in = task.token_input
        tokens_out = task.token_output
        tokens_in_str = (
            f"{tokens_in / 1000:.1f}k" if tokens_in >= 1000 else str(tokens_in)
        )
        tokens_out_str = (
            f"{tokens_out / 1000:.1f}k" if tokens_out >= 1000 else str(tokens_out)
        )

        agent_name = (self._shared.current_agent_name or "Agent").upper()
        phase = task.current_phase

        c_border = THEME["hud_border"]
        c_active = THEME["hud_active"]
        c_dim = THEME["hud_dim"]
        c_muted = THEME["hud_muted"]
        c_thinking = THEME["thinking"]
        c_executing = THEME["tool_pending"]

        phase_config = {
            "thinking": ("THINKING", c_thinking, "◐"),
            "executing": ("RUNNING", c_executing, "⚙"),
            "waiting": ("IDLE", c_muted, "○"),
            "idle": ("IDLE", c_muted, "○"),
        }
        label, color, icon = phase_config.get(phase, ("IDLE", c_muted, "○"))

        sep = f"[{c_border}]│[/]"
        spinner = HEADSET_BLINK_FRAMES[int(time.time() * 8) % len(HEADSET_BLINK_FRAMES)]

        return (
            f"[{c_border}]├─[/] [{color}]{spinner} {label}[/]  {sep}  "
            f"[{c_active}]{agent_name}[/]  {sep}  "
            f"[{c_dim}]T+{time_str}[/]  {sep}  "
            f"[{c_dim}]{tokens_in_str}↑ {tokens_out_str}↓[/]  {sep}  "
            f"[{c_muted}]ESC[/] [{c_dim}]cancel[/]"
        )
