"""
Tool renderer: military HUD-style tool execution display.
"""

from typing import Any, Optional
from rich.console import RenderableType, Group
from rich.text import Text

from .base import BaseRenderer
from ..state import TaskState, ToolState
from ..formatters import format_dict_inline, format_duration_hud
from ..theme import THEME
from ..core.responsive import ResponsiveWidth


class ToolRenderer(BaseRenderer):
    """Renders tool execution in military HUD style."""

    def __init__(self, console, verbosity):
        super().__init__(console, verbosity)
        self._c_border = THEME["hud_border"]
        self._c_dim = THEME["hud_dim"]
        self._c_muted = THEME["hud_muted"]
        self._c_text = THEME["hud_text"]
        self._c_success = THEME["hud_success"]
        self._c_error = THEME["hud_error"]
        self._c_pending = THEME["hud_pending"]

    def render(self, state: TaskState) -> Optional[RenderableType]:
        """Render all tools from all agents."""
        tools = []
        for agent in state.agents.values():
            for tool in agent.tools:
                tools.append(self.render_tool(tool))
        return Group(*tools) if tools else None

    def render_tool(self, tool: ToolState) -> RenderableType:
        """Render a single tool execution block in HUD style."""
        lines = []

        header = self._render_tool_header(tool)
        lines.append(header)

        if tool.input_data:
            input_line = self._render_input(tool.input_data)
            lines.append(input_line)

        if tool.status == "success" and tool.output_data:
            output_line = self._render_output(tool.output_data)
            lines.append(output_line)
        elif tool.status == "error" and tool.error:
            error_line = self._render_error(tool.error)
            lines.append(error_line)
        elif tool.status == "pending":
            spinner_line = Text()
            spinner_line.append("│   ", style=self._c_border)
            spinner_line.append("⟳ EXECUTING...", style=f"italic {self._c_pending}")
            lines.append(spinner_line)

        return Group(*lines)

    def _render_tool_header(self, tool: ToolState) -> Text:
        """Render HUD-style tool header."""
        line = Text()

        line.append("├─ ", style=self._c_border)

        if tool.status == "pending":
            line.append("◐ ", style=self._c_pending)
        elif tool.status == "success":
            line.append("● ", style=self._c_success)
        elif tool.status == "error":
            line.append("✗ ", style=self._c_error)
        else:
            line.append("◯ ", style=self._c_muted)

        name_style = self._c_error if tool.status == "error" else self._c_text
        line.append(tool.name, style=f"bold {name_style}")

        if tool.duration > 0:
            duration_str = format_duration_hud(tool.duration)
            line.append(f" T+{duration_str}", style=self._c_dim)

        return line

    def _render_input(self, input_data: dict) -> Text:
        """Render HUD-style tool input."""
        line = Text()
        line.append("│   ", style=self._c_border)
        line.append("▸ ", style=self._c_muted)

        cleaned_data = self._clean_input_data(input_data)
        line.append(format_dict_inline(cleaned_data), style=self._c_dim)
        return line

    def _clean_input_data(self, input_data: dict) -> dict:
        """Clean up input data for display."""
        import json

        cleaned = {}
        for key, value in input_data.items():
            if isinstance(value, str) and (
                value.strip().startswith("[") or value.strip().startswith("{")
            ):
                try:
                    parsed = json.loads(value.strip())
                    if isinstance(parsed, list) and len(parsed) > 0:
                        first = parsed[0]
                        if isinstance(first, dict) and "command" in first:
                            cleaned[key] = first["command"]
                            continue
                    elif isinstance(parsed, dict) and "command" in parsed:
                        cleaned[key] = parsed["command"]
                        continue
                except json.JSONDecodeError:
                    pass
            cleaned[key] = value
        return cleaned

    def _render_output(self, output_data: Any, duration: float | None = None) -> Text:
        """Render HUD-style tool output."""
        line = Text()
        line.append("│   ", style=self._c_border)
        line.append("◀ ", style=self._c_success)

        if isinstance(output_data, str):
            formatted = self._format_output_string(output_data)
            line.append(formatted, style=self._c_text)
        elif isinstance(output_data, dict):
            formatted = self._format_output_dict(output_data)
            line.append(formatted, style=self._c_text)
        else:
            line.append(str(output_data), style=self._c_text)

        if duration and duration > 0:
            duration_str = format_duration_hud(duration)
            line.append(f" T+{duration_str}", style=self._c_dim)

        return line

    def _format_output_string(self, output: str) -> str:
        """Format string output with HUD-style line breaks."""
        if not output:
            return "OK"

        output = output.strip()
        lines = [line for line in output.split("\n") if line.strip()]

        if not lines:
            return "OK"

        width = ResponsiveWidth.get_content_width(padding=8)
        if len(lines) == 1 and len(lines[0]) <= width:
            return lines[0]

        if len(lines) == 1:
            if width <= 3:
                return lines[0][:width]
            return lines[0][: width - 3] + "..."

        indent = "\n│       "
        formatted = lines[0]

        for line in lines[1:15]:
            formatted += f"{indent}{line.strip()}"

        if len(lines) > 15:
            formatted += f"{indent}... (+{len(lines) - 15} lines)"

        return formatted

    def _format_output_dict(self, output: dict) -> str:
        """Format dictionary output in HUD style."""
        if not output:
            return "OK"

        parts = []
        indent = "│       "

        for key, value in list(output.items())[:5]:
            if isinstance(value, list):
                parts.append(f"{key}: {len(value)} items")
            elif isinstance(value, dict):
                parts.append(f"{key}: {{...}}")
            elif isinstance(value, str) and len(str(value)) > 50:
                parts.append(f"{key}: {str(value)[:47]}...")
            else:
                parts.append(f"{key}: {value}")

        if len(output) > 5:
            parts.append(f"+{len(output) - 5} more")

        if len(parts) == 1:
            return parts[0]

        result = parts[0]
        for part in parts[1:]:
            result += f"\n{indent}{part}"

        return result

    def _render_error(self, error: str, duration: float | None = None) -> Text:
        """Render HUD-style tool error."""
        line = Text()
        line.append("│   ", style=self._c_border)
        line.append("✗ ", style=self._c_error)
        line.append(error, style=self._c_error)
        if duration and duration > 0:
            duration_str = format_duration_hud(duration)
            line.append(f" T+{duration_str}", style=self._c_dim)
        return line

    def render_tool_with_spinner(self, tool: ToolState) -> RenderableType:
        """Render a pending tool with HUD status."""
        if tool.status != "pending":
            return self.render_tool(tool)

        lines = [self._render_tool_header(tool)]

        if tool.input_data:
            lines.append(self._render_input(tool.input_data))

        return Group(*lines)
