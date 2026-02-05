"""
Thinking renderer: military HUD-style agent reasoning display.
"""

from typing import Optional
from rich.console import RenderableType
from rich.text import Text

from .base import BaseRenderer
from ..state import TaskState
from ..theme import THEME
from ..core.responsive import ResponsiveWidth


class ThinkingRenderer(BaseRenderer):
    """Renders agent thinking/reasoning in military HUD style."""

    def __init__(self, console, verbosity):
        super().__init__(console, verbosity)
        self._c_border = THEME["hud_border"]
        self._c_dim = THEME["hud_dim"]
        self._c_muted = THEME["hud_muted"]
        self._c_thinking = THEME["thinking"]

    def render(self, state: TaskState) -> Optional[RenderableType]:
        """Render current thinking from active agent."""
        if not state.active_agent_id:
            return None

        agent = state.agents.get(state.active_agent_id)
        if not agent or not agent.current_thought:
            return None

        return self.render_thought(agent.current_thought)

    def render_thought(
        self, thought: str, max_width: Optional[int] = None
    ) -> RenderableType:
        """Render a HUD-style thinking block."""
        if max_width is None:
            max_width = ResponsiveWidth.get_content_width(padding=8)
        wrapped = self._wrap_text(thought, max_width - 8)

        lines = []
        lines.append(
            Text.from_markup(f"[{self._c_border}]├─[/] [{self._c_muted}]ANALYZING[/]")
        )

        for line in wrapped.split("\n"):
            text = Text()
            text.append("│ ", style=self._c_border)
            text.append(line, style=f"italic {self._c_thinking}")
            lines.append(text)

        from rich.console import Group

        return Group(*lines)

    def render_inline(self, thought: str) -> Text:
        """Render HUD-style inline thought."""
        line = Text()
        line.append("├─ ", style=self._c_border)
        line.append("◐ ", style=self._c_thinking)
        line.append(thought, style=f"italic {self._c_thinking}")
        return line

    def _wrap_text(self, text: str, width: int) -> str:
        """Simple text wrapping."""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            if current_length + len(word) + 1 <= width:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_length = len(word)

        if current_line:
            lines.append(" ".join(current_line))

        return "\n".join(lines)
