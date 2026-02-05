"""
Interactive tool explorer for the dashboard.

This module implements a simple interactive explorer over executed tools.
"""

from __future__ import annotations

import json
from typing import Any, Dict

from rich.console import Console

from ..theme import ICONS, THEME
from .shared_state import DashboardSharedState


class ToolExplorer:
    """Interactive explorer for tool history."""

    def __init__(self, console: Console) -> None:
        self._console = console

    def start(self, shared: DashboardSharedState, print_raw: callable) -> None:
        """Launch an interactive tool explorer for the current task."""
        if not shared.tool_history:
            print_raw(f"[{THEME['muted']}]No tools executed.[/]")
            return

        self._console.print()
        print_raw(f"[bold {THEME['text']}]─── Tool Explorer ───[/]")
        print_raw(f"[{THEME['muted']}]Enter tool number to expand, 'q' to quit[/]")
        self._console.print()

        for idx, tool in enumerate(shared.tool_history, 1):
            status_icon = (
                ICONS["success"] if tool["status"] == "success" else ICONS["error"]
            )
            status_color = (
                THEME["tool_success"] if tool["status"] == "success" else THEME["error"]
            )
            print_raw(
                f"  [{status_color}]{status_icon}[/] [{THEME['muted']}]{idx}.[/] "
                f"[bold {THEME['text']}]{tool['name']}[/]"
            )

        self._console.print()

        while True:
            try:
                choice = self._console.input(f"[{THEME['text']}]› [/]").strip().lower()
                if choice in ("q", "quit", "exit", ""):
                    break
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(shared.tool_history):
                        self._print_tool_detail(shared.tool_history[idx], print_raw)
                    else:
                        print_raw(f"[{THEME['warning']}]Invalid number[/]")
            except (EOFError, KeyboardInterrupt):
                break

    def _print_tool_detail(self, tool: Dict[str, Any], print_raw: callable) -> None:
        self._console.print()
        print_raw(f"[bold {THEME['text']}]┌─ {tool['name']} ─┐[/]")

        print_raw(f"[{THEME['input']}]│ Input:[/]")
        if tool.get("input"):
            try:
                formatted = json.dumps(tool["input"], indent=2, default=str)
                for line in formatted.split("\n"):
                    print_raw(f"[{THEME['muted']}]│   [/]{line}")
            except Exception:
                print_raw(f"[{THEME['muted']}]│   [/]{tool['input']}")
        else:
            print_raw(f"[{THEME['muted']}]│   (none)[/]")

        print_raw(f"[{THEME['output']}]│ Output:[/]")
        if tool.get("output"):
            output_str = str(tool["output"])
            for line in output_str.split("\n"):
                print_raw(f"[{THEME['muted']}]│   [/]{line}")
        elif tool.get("error"):
            print_raw(f"[{THEME['error']}]│   {tool['error']}[/]")
        else:
            print_raw(f"[{THEME['muted']}]│   (none)[/]")

        print_raw(f"[{THEME['border']}]└{'─' * 40}┘[/]")
        self._console.print()
