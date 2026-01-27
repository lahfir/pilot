"""
Tool display management for the dashboard.

This module owns tool start/completion logging and printing. It preserves the
current behavior of printing a pending thought immediately before the first tool
line for an agent and supports nested tool rendering under that thought group.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional, Protocol

from rich.text import Text

from ..state import ToolState
from ..theme import ICONS, THEME
from ..core.responsive import ResponsiveWidth
from .shared_state import DashboardSharedState


class _AgentThoughtSource(Protocol):
    def consume_pending_thought_for_active_agent(self) -> Optional[str]: ...

    def print_pending_thought(self, thought: str, render_inline: callable) -> None: ...


class _Printer(Protocol):
    def _print(self, text: Text) -> None: ...

    def _print_raw(self, content: str) -> None: ...

    @property
    def console(self): ...


class _StatusSink(Protocol):
    def show(self, message: str = "") -> None: ...


class _ToolRendererPort(Protocol):
    def _render_tool_header(self, tool: ToolState) -> Text: ...

    def _render_input(self, input_data: Any) -> Text: ...

    def _render_output(
        self, output_data: Any, duration: float | None = None
    ) -> Text: ...

    def _render_error(self, error: str, duration: float | None = None) -> Text: ...


class _ThinkingRendererPort(Protocol):
    def render_inline(self, thought: str) -> Text: ...


class ToolDisplay:
    """Manage tool UI logging and printing."""

    def __init__(
        self,
        shared: DashboardSharedState,
        printer: _Printer,
        status: _StatusSink,
        agent_thoughts: _AgentThoughtSource,
        tool_renderer: _ToolRendererPort,
        thinking_renderer: _ThinkingRendererPort,
    ) -> None:
        self._shared = shared
        self._printer = printer
        self._status = status
        self._agent_thoughts = agent_thoughts
        self._tool_renderer = tool_renderer
        self._thinking_renderer = thinking_renderer

    def log_tool_start(self, tool_name: str, tool_input: Any) -> str:
        """Create tool state, store in history, and print tool start."""
        if not self._shared.task or not self._shared.task.active_agent_id:
            return ""
        if self._shared.current_agent_name == "Manager":
            return ""

        agent = self._shared.task.agents.get(self._shared.task.active_agent_id)
        if not agent:
            return ""

        tool = agent.add_tool(tool_name, tool_input)
        self._shared.task.total_tools += 1

        self._shared.tool_history.append(
            {
                "id": tool.tool_id,
                "name": tool_name,
                "input": tool_input,
                "output": None,
                "error": None,
                "status": "pending",
                "timestamp": time.time(),
            }
        )

        self._print_tool_start(tool)
        return tool.tool_id

    def get_pending_tool_id(self, tool_name: str | None = None) -> Optional[str]:
        """Find the most recent pending tool for the active agent."""
        if not self._shared.task or not self._shared.task.active_agent_id:
            return None
        agent = self._shared.task.agents.get(self._shared.task.active_agent_id)
        if not agent:
            return None
        for tool in reversed(agent.tools):
            if tool.status == "pending" and (
                tool_name is None or tool.name == tool_name
            ):
                return tool.tool_id
        return None

    def reset_tool_timer(self, tool_name: str | None = None) -> None:
        """Reset the start time for the most recent pending tool."""
        if not self._shared.task or not self._shared.task.active_agent_id:
            return
        agent = self._shared.task.agents.get(self._shared.task.active_agent_id)
        if not agent:
            return
        for tool in reversed(agent.tools):
            if tool.status == "pending" and (
                tool_name is None or tool.name == tool_name
            ):
                tool.start_time = time.time()
                return

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
        """Complete tool state, update history, and print tool result."""
        if not self._shared.task:
            return

        tool = None
        for agent in self._shared.task.agents.values():
            tool = agent.get_tool(tool_id)
            if tool:
                break

        if not tool:
            for agent in self._shared.task.agents.values():
                for t in reversed(agent.tools):
                    if t.status == "pending":
                        tool = t
                        break
                if tool:
                    break

        if not tool:
            return

        output = (
            action_taken
            or data
            or (f"method={method_used}" if method_used else "success")
        )
        tool.complete(success, output, error)

        if not success and self._shared.task:
            self._shared.task.failed_tools += 1

        for hist in self._shared.tool_history:
            if hist["id"] == tool.tool_id:
                hist["output"] = output
                hist["error"] = error
                hist["status"] = "success" if success else "error"
                break

        self._print_tool_complete(tool)

    def _nest_tool_line(self, line: Text) -> Text:
        nested = Text()
        nested.append("│   ", style=THEME["hud_border"])
        nested.append_text(line)
        return nested

    def _print_tool_start(self, tool: ToolState) -> None:
        if tool.tool_id in self._shared.started_tools:
            return
        self._shared.started_tools.add(tool.tool_id)

        is_nested = False
        pending = self._agent_thoughts.consume_pending_thought_for_active_agent()
        if pending:
            self._agent_thoughts.print_pending_thought(
                pending, self._thinking_renderer.render_inline
            )
            self._shared.nested_tools.add(tool.tool_id)
            is_nested = True

        if not is_nested:
            action_desc = self._get_action_description(tool.name, tool.input_data)
            if action_desc:
                action_line = Text()
                action_line.append(
                    f"  {ICONS['bullet']} ", style=f"bold {THEME['tool_pending']}"
                )
                action_line.append(action_desc, style=f"italic {THEME['text']}")
                self._printer._print(action_line)

        pending_line = Text()
        pending_line.append("├─ ", style=THEME["hud_border"])
        pending_line.append("⟳ ", style=THEME["tool_pending"])
        pending_line.append(tool.name, style=f"bold {THEME['text']}")

        self._printer._print(
            self._nest_tool_line(pending_line) if is_nested else pending_line
        )
        self._status.show(f"Running {tool.name}...")

    def _print_tool_complete(self, tool: ToolState) -> None:
        is_nested = tool.tool_id in self._shared.nested_tools

        if tool.tool_id not in self._shared.printed_tools:
            header = self._tool_renderer._render_tool_header(tool)
            self._printer._print(self._nest_tool_line(header) if is_nested else header)
            if tool.input_data:
                input_line = self._tool_renderer._render_input(tool.input_data)
                self._printer._print(
                    self._nest_tool_line(input_line) if is_nested else input_line
                )
            self._shared.printed_tools.add(tool.tool_id)

        if tool.status == "success":
            output_line = self._tool_renderer._render_output(
                tool.output_data, tool.duration
            )
            self._printer._print(
                self._nest_tool_line(output_line) if is_nested else output_line
            )
            self._printer._print_raw("")
            self._status.show("Processing results...")
        else:
            error_line = self._tool_renderer._render_error(
                tool.error or "Unknown error", tool.duration
            )
            self._printer._print(
                self._nest_tool_line(error_line) if is_nested else error_line
            )
            self._printer._print_raw("")
            self._status.show("Handling error...")

        self._shared.started_tools.discard(tool.tool_id)
        if is_nested:
            self._shared.nested_tools.discard(tool.tool_id)

    def _get_action_description(self, tool_name: str, input_data: Dict) -> str:
        if not input_data:
            return ""

        import json

        data = input_data.get("value", input_data)
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                data = {"value": data}

        if isinstance(data, list) and data:
            data = data[0] if isinstance(data[0], dict) else {"value": data}

        explanation = data.get("explanation") if isinstance(data, dict) else None
        if isinstance(explanation, str) and len(explanation) > 5:
            return explanation[:120] + ("..." if len(explanation) > 120 else "")

        action_map = {
            "open_application": lambda d: f"Opening {d.get('app_name', 'application')}",
            "check_app_running": lambda d: f"Checking if {d.get('app_name', 'app')} is running",
            "click_element": lambda d: f"Clicking {d.get('target', d.get('element_id', 'element'))}",
            "type_text": lambda d: f"Typing text into {d.get('target', 'field')}",
            "read_screen_text": lambda d: f"Reading text from {d.get('app_name', 'screen')}",
            "get_accessible_elements": lambda d: f"Scanning {d.get('app_name', 'app')} UI",
            "take_screenshot": lambda d: "Taking screenshot",
            "scroll": lambda d: f"Scrolling {d.get('direction', 'down')}",
            "web_automation": lambda d: ResponsiveWidth.truncate(
                str(d.get("task", "Running web automation")),
                max_ratio=0.7,
                min_width=40,
            ),
            "execute_shell_command": lambda d: "Executing command",
            "human_assistance": lambda d: f"⚠️ {d.get('reason', 'Requesting human help')}",
            "request_human_assistance": lambda d: f"⚠️ {d.get('reason', 'Requesting human help')}",
            "request_human_input": lambda d: f"⚠️ {d.get('prompt', 'Requesting input')}",
            "delegate_task": lambda d: f"Delegating to {d.get('agent', 'agent')}",
            "coding_task": lambda d: ResponsiveWidth.truncate(
                str(d.get("task", "Running coding task")), max_ratio=0.7, min_width=40
            ),
        }

        if tool_name in action_map:
            try:
                return action_map[tool_name](data)
            except Exception:
                return ""

        return ""
