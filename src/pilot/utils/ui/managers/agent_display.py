"""
Agent display management for the dashboard.

This module owns agent switching, reasoning updates, and agent summary/header
printing. It stores pending thoughts to be printed immediately before the first
tool line for an agent, preserving the current output structure.
"""

from __future__ import annotations

from typing import Optional, Protocol

from rich.console import Console
from rich.text import Text

from ..state import AgentState, TaskState
from ..formatters import format_duration_status
from ..theme import THEME
from ..core.responsive import ResponsiveWidth
from .shared_state import DashboardSharedState


class _AgentPrinter(Protocol):
    def _print(self, text: Text) -> None: ...

    def _print_raw(self, content: str) -> None: ...


class _StatusSink(Protocol):
    def show(self, message: str = "") -> None: ...


class AgentDisplay:
    """Handle agent-level UI changes and printing."""

    def __init__(
        self,
        console: Console,
        shared: DashboardSharedState,
        printer: _AgentPrinter,
        status: _StatusSink,
    ) -> None:
        self._console = console
        self._shared = shared
        self._printer = printer
        self._status = status

    def get_current_agent_name(self) -> str:
        """Get the current agent display name."""
        return self._shared.current_agent_name or ""

    def set_agent(self, agent_name: str) -> None:
        """Switch the active agent and print headers/summaries as needed."""
        if not self._shared.task:
            return

        agent_name = agent_name.strip()
        if agent_name in {"Manager", "Task Orchestration Manager"}:
            agent_name = "Manager"

        if agent_name == self._shared.current_agent_name:
            return

        was_manager = self._shared.current_agent_name == "Manager"
        previous_agent_id = self._shared.task.active_agent_id

        if self._shared.current_agent_name and previous_agent_id:
            prev_agent = self._shared.task.agents.get(previous_agent_id)
            if prev_agent:
                if was_manager and agent_name != "Manager":
                    self._print_delegation(agent_name)
                self.print_agent_summary(prev_agent)

        self._shared.current_agent_name = agent_name
        self._shared.last_thought_hash = None
        self._shared.pending_thought = None
        self._shared.pending_thought_agent_id = None

        agent = self._shared.task.set_active_agent(agent_name)
        if agent.agent_id not in self._shared.printed_agents:
            self._shared.printed_agents.add(agent.agent_id)
            self.print_agent_header(agent)
            self._status.show(f"{agent_name} analyzing...")

    def set_thinking(self, thought: str) -> None:
        """Update the active agent's reasoning and set pending thought for printing."""
        if not self._shared.task or not self._shared.task.active_agent_id:
            return
        if not thought or not thought.strip():
            return

        thought = thought.strip()
        if self._is_system_prompt_leak(thought):
            return

        thought_hash = hash(thought[:100])
        if thought_hash == self._shared.last_thought_hash:
            return
        self._shared.last_thought_hash = thought_hash

        agent = self._shared.task.agents.get(self._shared.task.active_agent_id)
        if not agent:
            return

        agent.current_thought = thought
        agent.status = "thinking"
        self._shared.pending_thought = thought
        self._shared.pending_thought_agent_id = agent.agent_id

        short_thought = thought[:60] + "..." if len(thought) > 60 else thought
        self._status.show(short_thought)

    def consume_pending_thought_for_active_agent(self) -> Optional[str]:
        """Return and clear pending thought if it belongs to the active agent."""
        if (
            not self._shared.task
            or not self._shared.task.active_agent_id
            or not self._shared.pending_thought
            or not self._shared.pending_thought_agent_id
        ):
            return None

        active = self._shared.task.agents.get(self._shared.task.active_agent_id)
        if not active or active.agent_id != self._shared.pending_thought_agent_id:
            return None

        thought = self._shared.pending_thought
        self._shared.pending_thought = None
        self._shared.pending_thought_agent_id = None
        return thought

    def print_pending_thought(self, thought: str, render_inline: callable) -> None:
        """Print a full thought line using the provided thinking renderer."""
        cleaned = thought.strip()
        if not cleaned:
            return
        self._printer._print_raw("")
        line = render_inline(cleaned)
        self._printer._print(line)

    def log_delegation(self, agent_name: str, task_summary: str) -> None:
        """Print a delegation line for manager handoff."""
        if not self._shared.task:
            return
        line = Text()
        line.append("  → ", style=f"bold {THEME['agent_active']}")
        line.append("Delegating to ", style=THEME["muted"])
        line.append(agent_name, style=f"bold {THEME['agent_active']}")
        line.append(": ", style=THEME["muted"])
        task_summary = ResponsiveWidth.truncate(
            task_summary, max_ratio=0.6, min_width=40
        )
        line.append(task_summary, style=THEME["text"])
        self._printer._print(line)

    def print_agent_header(self, agent: AgentState) -> None:
        """Print the HUD-style agent header."""
        self._print_agent_header(agent)

    def print_agent_summary(self, agent: AgentState) -> None:
        """Print the HUD-style agent completion summary."""
        self._print_agent_summary(agent)

    def _print_delegation(self, target_agent: str) -> None:
        line = Text()
        line.append("\n  → ", style=f"bold {THEME['agent_active']}")
        line.append("Delegating to ", style=THEME["muted"])
        line.append(target_agent, style=f"bold {THEME['agent_active']}")
        self._printer._print(line)

    def _print_agent_header(self, agent: AgentState) -> None:
        c_border = THEME["hud_border"]
        c_active = THEME["hud_active"]
        c_text = THEME["hud_text"]

        w = self._console.width
        name = agent.name.upper()
        status = "ACTIVE"

        self._printer._print_raw("")
        self._printer._print_raw("")
        self._printer._print_raw(f"[{c_border}]╭{'─' * (w - 2)}╮[/]")

        inner = w - 4
        left = f"[{c_active}]●[/] [{c_text}]{name}[/]"
        right = f"[{c_active}]{status}[/]"
        left_len = len(name) + 2
        right_len = len(status)
        pad = inner - left_len - right_len
        self._printer._print_raw(
            f"[{c_border}]│[/] {left}{' ' * pad}{right} [{c_border}]│[/]"
        )
        self._printer._print_raw(f"[{c_border}]╰{'─' * (w - 2)}╯[/]")
        self._printer._print_raw("")

    def _print_agent_summary(self, agent: AgentState) -> None:
        c_border = THEME["hud_border"]
        c_success = THEME["hud_success"]
        c_dim = THEME["hud_dim"]
        c_text = THEME["hud_text"]

        self._printer._print_raw("")

        duration_str = format_duration_status(agent.duration)

        total_tools = len(agent.tools)
        success_tools = sum(1 for t in agent.tools if t.status == "success")

        summary = Text()
        summary.append("╰─ ", style=c_border)
        summary.append("● ", style=c_success)
        summary.append(agent.name.upper(), style=f"bold {c_text}")
        summary.append(" ─ ", style=c_border)
        summary.append("COMPLETE", style=f"bold {c_success}")
        summary.append("  │  ", style=c_border)
        summary.append(f"T+{duration_str}", style=c_dim)
        summary.append("  │  ", style=c_border)
        summary.append(f"OPS:{success_tools}/{total_tools}", style=c_dim)

        self._printer._print(summary)
        self._printer._print_raw("")
        self._printer._print_raw("")

    def _is_system_prompt_leak(self, text: str) -> bool:
        leak_patterns = [
            "Tool Name:",
            "Tool Arguments:",
            "Tool Description:",
            "IMPORTANT: Use the following format",
            "you should always think about what to do",
            "You ONLY have access to the following tools",
        ]
        return any(pattern in text for pattern in leak_patterns)

    def get_task(self) -> Optional[TaskState]:
        """Return the current task state (if any)."""
        return self._shared.task
