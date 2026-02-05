"""
Agent renderer: military HUD-style agent status display.
"""

from typing import Optional, List
from rich.console import RenderableType, Group
from rich.text import Text

from .base import BaseRenderer
from ..state import TaskState, AgentState
from ..theme import THEME
from ..core.responsive import ResponsiveWidth


class AgentRenderer(BaseRenderer):
    """Renders agent status in military HUD style."""

    def __init__(self, console, verbosity):
        super().__init__(console, verbosity)
        self._c_border = THEME["hud_border"]
        self._c_dim = THEME["hud_dim"]
        self._c_muted = THEME["hud_muted"]
        self._c_text = THEME["hud_text"]
        self._c_active = THEME["hud_active"]
        self._c_success = THEME["hud_success"]
        self._c_error = THEME["hud_error"]
        self._c_thinking = THEME["thinking"]

    def render(self, state: TaskState) -> Optional[RenderableType]:
        """Render all agents in HUD style."""
        if not state.agents:
            return None

        panels = []
        for agent_id in state.agents:
            agent = state.agents[agent_id]
            panel = self._render_agent_block(agent, agent_id == state.active_agent_id)
            panels.append(panel)

        return Group(*panels)

    def _render_agent_block(self, agent: AgentState, is_active: bool) -> RenderableType:
        """Render a single agent as HUD block."""
        lines = []

        status_text, status_style = self._get_status_display(agent, is_active)
        name = agent.name.upper()

        header = Text()
        header.append("╠═ ", style=self._c_border)
        if is_active:
            header.append("● ", style=self._c_active)
        else:
            header.append("◯ ", style=self._c_muted)
        header.append(name, style=f"bold {self._c_text}")
        header.append(" ─ ", style=self._c_border)
        header.append(status_text, style=status_style)

        lines.append(header)

        content = self._build_agent_content(agent, is_active)
        if content:
            lines.append(content)

        return Group(*lines)

    def _get_status_display(
        self, agent: AgentState, is_active: bool
    ) -> tuple[str, str]:
        """Get HUD-style status text and style."""
        status_map = {
            "idle": ("STANDBY", self._c_muted),
            "thinking": ("ANALYZING", self._c_thinking),
            "executing": ("EXECUTING", self._c_active),
            "complete": ("COMPLETE", self._c_success),
            "error": ("ERROR", self._c_error),
        }

        if is_active and agent.status in ("idle", "thinking"):
            return ("ACTIVE", f"bold {self._c_active}")

        return status_map.get(agent.status, ("", self._c_muted))

    def _build_agent_content(
        self, agent: AgentState, is_active: bool
    ) -> Optional[RenderableType]:
        """Build HUD-style agent content."""
        lines: List[RenderableType] = []

        if is_active and agent.current_thought:
            thought_text = Text()
            thought_text.append("│  ", style=self._c_border)
            thought_text.append("◐ ", style=self._c_thinking)
            thought = ResponsiveWidth.truncate(
                agent.current_thought, max_ratio=0.9, min_width=60
            )
            thought_text.append(thought, style=f"italic {self._c_thinking}")
            lines.append(thought_text)

        if agent.tools:
            from .tool import ToolRenderer

            tool_renderer = ToolRenderer(self.console, self.verbosity)
            for tool in agent.tools:
                tool_display = tool_renderer.render_tool(tool)
                lines.append(tool_display)

        if not lines and is_active:
            waiting = Text()
            waiting.append("│  ", style=self._c_border)
            waiting.append("⟳ AWAITING ORDERS...", style=f"italic {self._c_muted}")
            lines.append(waiting)

        return Group(*lines) if lines else None

    def render_compact(self, agent: AgentState, is_active: bool) -> Text:
        """Render HUD-style compact agent summary."""
        line = Text()

        if is_active:
            line.append("● ", style=self._c_active)
        else:
            line.append("◯ ", style=self._c_muted)

        name_style = f"bold {self._c_active}" if is_active else self._c_muted
        line.append(agent.name.upper(), style=name_style)

        if agent.tools:
            success = sum(1 for t in agent.tools if t.status == "success")
            total = len(agent.tools)
            line.append(f" OPS:{success}/{total}", style=self._c_dim)

        return line
