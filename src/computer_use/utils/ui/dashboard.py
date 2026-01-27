"""
Dashboard facade.

This module provides the public DashboardManager API while delegating most
responsibilities to focused manager modules. The goal is to keep each file under
the project size limit and to make the rendering backend swappable.
"""

from __future__ import annotations

import sys
import threading
from typing import Any, Dict, Optional

from rich.console import Console
from rich.text import Text

from .core import RenderManager
from .managers import (
    AgentDisplay,
    DashboardSharedState,
    LogBatcher,
    StatusManager,
    TaskManager,
    ToolDisplay,
)
from .managers.session_log import SessionLogPrinter
from .managers.tool_explorer import ToolExplorer
from .renderers import AgentRenderer, StatusBarRenderer, ThinkingRenderer, ToolRenderer
from .state import ActionType, VerbosityLevel
from .theme import ICONS, THEME


class DashboardManager:
    """
    Singleton dashboard manager.

    The public methods are intentionally stable because they are called from
    `main.py`, `crew.py`, and various tools. Internals are delegated to smaller
    components in `ui/managers/`.
    """

    _instance: Optional["DashboardManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "DashboardManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._initialized = True

        self.console = Console(force_terminal=True, force_interactive=True)
        self.verbosity = VerbosityLevel.NORMAL

        self._render_manager = RenderManager()
        self._render_manager.bind_console(self.console)

        self._shared = DashboardSharedState()
        self._state_lock = threading.Lock()

        self._thinking_renderer = ThinkingRenderer(self.console, self.verbosity)
        self._tool_renderer = ToolRenderer(self.console, self.verbosity)
        self._agent_renderer = AgentRenderer(self.console, self.verbosity)
        self._status_renderer = StatusBarRenderer(self.console, self.verbosity)

        self._status_manager = StatusManager(
            self.console, self._shared, self._render_manager
        )
        self._task_manager = TaskManager(self.console, self._shared, self)
        self._agent_display = AgentDisplay(
            self.console, self._shared, self, self._status_manager
        )
        self._tool_display = ToolDisplay(
            self._shared,
            self,
            self._status_manager,
            self._agent_display,
            self._tool_renderer,
            self._thinking_renderer,
        )

        self._session_log = SessionLogPrinter(self.console)
        self._tool_explorer = ToolExplorer(self.console)

    @property
    def is_quiet(self) -> bool:
        return self.verbosity == VerbosityLevel.QUIET

    @property
    def is_verbose(self) -> bool:
        return self.verbosity == VerbosityLevel.VERBOSE

    def set_verbosity(self, level: VerbosityLevel) -> None:
        self.verbosity = level

    def _flush(self) -> None:
        sys.stdout.flush()
        sys.stderr.flush()

    def _print(self, text: Text) -> None:
        self._status_manager.pause()
        if self._shared.is_running:
            self._render_manager.append(text)
        else:
            self.console.print(text)
        self._flush()

    def _print_raw(self, content: str) -> None:
        self._status_manager.pause()
        if self._shared.is_running:
            self._render_manager.append_text(content)
        else:
            self.console.print(content)
        self._flush()

    def set_task(self, description: str) -> None:
        self._stop_live_status()
        self._task_manager.set_task(description)

    def start_dashboard(self) -> None:
        if self.is_quiet:
            return
        self._render_manager.clear()
        self._render_manager.start()
        self._task_manager.start_dashboard()
        self._print_header_once()
        self._start_live_status()

    def stop_dashboard(self, print_log: bool = True, cancelled: bool = False) -> None:
        self._shared.is_running = False
        self._stop_live_status()

        if self._shared.task and self._shared.task.active_agent_id and not cancelled:
            final_agent = self._shared.task.agents.get(
                self._shared.task.active_agent_id
            )
            if final_agent and final_agent.tools:
                pending = self._agent_display.consume_pending_thought_for_active_agent()
                if pending:
                    self._agent_display.print_pending_thought(
                        pending, self._thinking_renderer.render_inline
                    )
                self._agent_display.print_agent_summary(final_agent)

        if print_log and self._shared.task and not cancelled:
            self.console.print()
            self.print_session_log()
        self._render_manager.stop()

    def complete_task(self, success: bool = True) -> None:
        self._task_manager.complete_task(success)

    def get_current_agent_name(self) -> str:
        return self._agent_display.get_current_agent_name()

    def set_agent(self, agent_name: str) -> None:
        with self._state_lock:
            self._agent_display.set_agent(agent_name)

    def set_thinking(self, thought: str) -> None:
        with self._state_lock:
            self._agent_display.set_thinking(thought)

    def set_phase(self, phase: str, operation: Optional[str] = None) -> None:
        with self._state_lock:
            if self._shared.task:
                self._shared.task.set_phase(phase, operation)

    def set_action(self, action: str, target: Optional[str] = None) -> None:
        with self._state_lock:
            if not self._shared.task or not self._shared.task.active_agent_id:
                return
            agent = self._shared.task.agents.get(self._shared.task.active_agent_id)
            if agent:
                agent.status = "executing"

    def clear_action(self) -> None:
        return

    def log_delegation(self, agent_name: str, task_summary: str) -> None:
        with self._state_lock:
            self._agent_display.log_delegation(agent_name, task_summary)

    def log_llm_start(self, model: str) -> Optional[str]:
        with self._state_lock:
            if not self._shared.task or not self._shared.task.active_agent_id:
                return None
            agent = self._shared.task.agents.get(self._shared.task.active_agent_id)
            if not agent:
                return None
            llm_call = agent.start_llm_call(model)
            self._shared.task.set_phase("thinking", model)
            return llm_call.call_id

    def log_llm_complete(
        self, prompt_tokens: int = 0, completion_tokens: int = 0
    ) -> None:
        with self._state_lock:
            if not self._shared.task or not self._shared.task.active_agent_id:
                return
            agent = self._shared.task.agents.get(self._shared.task.active_agent_id)
            if agent:
                agent.complete_llm_call(prompt_tokens, completion_tokens)
            self._shared.task.set_phase("executing")

    def get_current_llm_elapsed(self) -> Optional[float]:
        if not self._shared.task or not self._shared.task.active_agent_id:
            return None
        agent = self._shared.task.agents.get(self._shared.task.active_agent_id)
        if not agent:
            return None
        llm_call = agent.get_active_llm_call()
        return llm_call.elapsed if llm_call else None

    def is_llm_active(self) -> bool:
        if not self._shared.task or not self._shared.task.active_agent_id:
            return False
        agent = self._shared.task.agents.get(self._shared.task.active_agent_id)
        return bool(agent and agent.get_active_llm_call() is not None)

    def log_tool_start(self, tool_name: str, tool_input: Any) -> str:
        with self._state_lock:
            return self._tool_display.log_tool_start(tool_name, tool_input)

    def get_pending_tool_id(self, tool_name: str = None) -> Optional[str]:
        return self._tool_display.get_pending_tool_id(tool_name)

    def reset_tool_timer(self, tool_name: str = None) -> None:
        with self._state_lock:
            self._tool_display.reset_tool_timer(tool_name)

    def log_tool_complete(
        self,
        tool_id: str,
        success: bool,
        action_taken: str = "",
        method_used: str = "",
        confidence: float = 0.0,
        error: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        with self._state_lock:
            self._tool_display.log_tool_complete(
                tool_id,
                success,
                action_taken=action_taken,
                method_used=method_used,
                confidence=confidence,
                error=error,
                data=data,
            )

    def update_token_usage(self, input_tokens: int, output_tokens: int) -> None:
        with self._state_lock:
            if self._shared.task:
                self._shared.task.token_input = input_tokens
                self._shared.task.token_output = output_tokens

    def _print_header_once(self) -> None:
        """Print a simple task header at the start of execution."""
        if not self._shared.task or not self._shared.is_running:
            return

        task = self._shared.task
        c_border = THEME["hud_border"]
        c_active = THEME["hud_active"]
        c_text = THEME["hud_text"]

        self.console.print()
        self.console.print(
            f"[{c_border}]╭─[/] [{c_active}]Starting hierarchical execution[/]"
        )
        self.console.print(f"[{c_border}]│[/]  [{c_text}]{task.description}[/]")
        self.console.print(f"[{c_border}]╰{'─' * 60}[/]")
        self.console.print()

    def _start_live_status(self) -> None:
        self._status_manager.start()

    def _stop_live_status(self) -> None:
        self._status_manager.stop()

    def _show_status(self, message: str = "") -> None:
        self._status_manager.show(message)

    def print_session_log(self) -> None:
        self._session_log.print_session_log(self._shared, self._print_raw)

    def start_tool_explorer(self) -> None:
        self._tool_explorer.start(self._shared, self._print_raw)

    def add_log_entry(
        self,
        action_type: ActionType,
        message: str,
        target: Optional[str] = None,
        status: str = "pending",
    ) -> int:
        if self._shared.is_running:
            line = Text()
            if status == "error":
                line.append(f"  {ICONS['error']} ", style=f"bold {THEME['error']}")
                line.append(message, style=THEME["error"])
            else:
                line.append(f"  {ICONS['bullet']} ", style=THEME["muted"])
                line.append(message, style=THEME["text"])
            self._print(line)
        return 0

    def update_log_entry(self, idx: int, status: str) -> None:
        return

    def set_steps(self, current: int, total: int) -> None:
        return

    def set_last_result(self, result: str) -> None:
        return

    def show_human_assistance(self, reason: str, instructions: str) -> None:
        return

    def hide_human_assistance(self) -> None:
        return

    def show_command_approval(self, command: str) -> None:
        return

    def hide_command_approval(self) -> None:
        return

    def set_browser_session(self, active: bool, profile: Optional[str] = None) -> None:
        if self._shared.task and active:
            self._shared.task.browser_agent_executed = True
            self._shared.task.external_tools_executed = True

    def mark_external_tool_executed(self) -> None:
        if self._shared.task:
            self._shared.task.external_tools_executed = True

    def has_external_work_executed(self) -> bool:
        if not self._shared.task:
            return False
        return (
            self._shared.task.external_tools_executed
            or self._shared.task.browser_agent_executed
        )

    def refresh(self) -> None:
        self._show_status()


dashboard = DashboardManager()
console = dashboard.console

__all__ = [
    "DashboardManager",
    "LogBatcher",
    "dashboard",
    "console",
]
