"""
Status bar renderer: military-grade HUD footer with metrics.
"""

from typing import Optional
from rich.console import RenderableType
from rich.text import Text

from .base import BaseRenderer
from ..state import TaskState
from ..formatters import format_duration_status, format_token_count
from ..theme import THEME


class StatusBarRenderer(BaseRenderer):
    """Renders the HUD-style status bar with current metrics."""

    def __init__(self, console, verbosity):
        super().__init__(console, verbosity)
        self._c_border = THEME["hud_border"]
        self._c_muted = THEME["hud_muted"]
        self._c_dim = THEME["hud_dim"]
        self._c_text = THEME["hud_text"]
        self._c_active = THEME["hud_active"]
        self._c_success = THEME["hud_success"]
        self._c_error = THEME["hud_error"]

    def render(self, state: TaskState) -> Optional[RenderableType]:
        """Render the HUD status bar."""
        return self._build_status_line(state)

    def _build_status_line(self, state: TaskState) -> Text:
        """Build the HUD-style status bar."""
        line = Text()

        line.append("╠", style=self._c_border)
        line.append("═", style=self._c_border)

        if state.active_agent_id:
            agent = state.agents.get(state.active_agent_id)
            if agent:
                line.append(" ● ", style=self._c_active)
                line.append(agent.name.upper(), style=f"bold {self._c_text}")
                line.append(" ─ ", style=self._c_border)
                status_style = self._get_status_style(agent.status)
                line.append(agent.status.upper(), style=status_style)
        else:
            line.append(" ◯ ", style=self._c_muted)
            line.append("STANDBY", style=self._c_muted)

        line.append(" ═╪═ ", style=self._c_border)

        duration_str = format_duration_status(state.duration)
        line.append("T+", style=self._c_muted)
        line.append(duration_str, style=self._c_text)

        line.append(" ═╪═ ", style=self._c_border)

        success = state.total_tools - state.failed_tools
        line.append("OPS:", style=self._c_muted)
        if state.failed_tools > 0:
            line.append(f"{success}", style=self._c_success)
            line.append(f"/{state.total_tools}", style=self._c_text)
            line.append(f" ✗{state.failed_tools}", style=self._c_error)
        else:
            line.append(f"{success}/{state.total_tools}", style=self._c_text)

        line.append(" ═╪═ ", style=self._c_border)

        total_tokens = state.token_input + state.token_output
        if total_tokens > 0:
            in_str = format_token_count(state.token_input)
            out_str = format_token_count(state.token_output)
            line.append(f"{in_str}↑ {out_str}↓", style=self._c_dim)

        line.append(" ═╪═ ", style=self._c_border)
        line.append("ESC", style=self._c_muted)
        line.append(" cancel", style=self._c_dim)

        return line

    def _get_status_style(self, status: str) -> str:
        """Get style for status text."""
        styles = {
            "idle": self._c_muted,
            "thinking": f"bold {THEME['thinking']}",
            "executing": f"bold {self._c_active}",
            "complete": f"bold {self._c_success}",
            "error": f"bold {self._c_error}",
        }
        return styles.get(status, self._c_muted)

    def render_inline(self, state: TaskState) -> str:
        """Render as a plain string for terminal status line."""
        parts = []

        if state.active_agent_id:
            agent = state.agents.get(state.active_agent_id)
            if agent:
                parts.append(f"● {agent.name} ─ {agent.status.upper()}")
        else:
            parts.append("◯ STANDBY")

        parts.append(f"T+{format_duration_status(state.duration)}")

        success = state.total_tools - state.failed_tools
        if state.failed_tools > 0:
            parts.append(f"OPS:{success}/{state.total_tools} ✗{state.failed_tools}")
        else:
            parts.append(f"OPS:{success}/{state.total_tools}")

        total_tokens = state.token_input + state.token_output
        if total_tokens > 0:
            in_str = format_token_count(state.token_input)
            out_str = format_token_count(state.token_output)
            parts.append(f"{in_str}↑ {out_str}↓")

        parts.append("ESC cancel")

        return " ═╪═ ".join(parts)
