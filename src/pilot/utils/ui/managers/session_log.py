"""
Session log printing for the dashboard.

This module prints the final session summary after task completion.
"""

from __future__ import annotations

from rich.console import Console

from ..theme import THEME
from .shared_state import DashboardSharedState


class SessionLogPrinter:
    """Print a session summary for the current task."""

    def __init__(self, console: Console) -> None:
        self._console = console

    def print_session_log(
        self, shared: DashboardSharedState, print_raw: callable
    ) -> None:
        """Print the complete session summary with timing breakdown."""
        if not shared.task:
            return

        task = shared.task
        print_raw(f"\n[{THEME['border']}]{'═' * 70}[/]")
        print_raw(f"[bold {THEME['text']}]  SESSION SUMMARY[/]")
        print_raw(f"[{THEME['border']}]{'═' * 70}[/]")

        duration = task.duration
        if duration < 60:
            duration_str = f"{int(duration)}s"
        else:
            mins = int(duration // 60)
            secs = int(duration % 60)
            duration_str = f"{mins}m {secs}s"

        success = task.total_tools - task.failed_tools
        stats = (
            f"  Duration: {duration_str} │ "
            f"Tools: {success}/{task.total_tools} │ "
            f"Tokens: {task.token_input}↑ {task.token_output}↓ │ "
            f"Agents: {len(task.agents)}"
        )
        print_raw(f"[{THEME['muted']}]{stats}[/]")

        llm_time = task.total_llm_time
        tool_time = task.total_tool_time
        total_tracked = llm_time + tool_time
        other_time = max(0, duration - total_tracked)

        if total_tracked > 0:
            llm_pct = (llm_time / duration * 100) if duration > 0 else 0
            tool_pct = (tool_time / duration * 100) if duration > 0 else 0
            other_pct = (other_time / duration * 100) if duration > 0 else 0

            def fmt_time(t: float) -> str:
                if t < 1:
                    return f"{t:.1f}s"
                if t < 60:
                    return f"{int(t)}s"
                return f"{int(t // 60)}m {int(t % 60)}s"

            timing_stats = (
                f"  Time Breakdown: "
                f"LLM {fmt_time(llm_time)} ({llm_pct:.0f}%) │ "
                f"Tools {fmt_time(tool_time)} ({tool_pct:.0f}%) │ "
                f"Other {fmt_time(other_time)} ({other_pct:.0f}%) │ "
                f"LLM Calls: {task.total_llm_calls}"
            )
            print_raw(f"[{THEME['muted']}]{timing_stats}[/]")

        print_raw(f"[{THEME['border']}]{'═' * 70}[/]")

        if task.agents:
            print_raw(f"[bold {THEME['text']}]  AGENT BREAKDOWN[/]")
            print_raw(f"[{THEME['border']}]{'─' * 70}[/]")

            for agent in task.agents.values():
                agent_llm = agent.total_llm_time
                agent_tool = agent.total_tool_time
                agent_calls = agent.llm_call_count
                tool_count = len(
                    [t for t in agent.tools if t.status in ("success", "error")]
                )

                def fmt_time(t: float) -> str:
                    if t < 1:
                        return f"{t:.1f}s"
                    if t < 60:
                        return f"{int(t)}s"
                    return f"{int(t // 60)}m {int(t % 60)}s"

                agent_line = (
                    f"  {agent.name:<14} │ "
                    f"{fmt_time(agent.duration):>6} │ "
                    f"LLM: {fmt_time(agent_llm):>5} ({agent_calls} calls) │ "
                    f"Tools: {fmt_time(agent_tool):>5} ({tool_count} calls)"
                )
                print_raw(f"[{THEME['muted']}]{agent_line}[/]")

            print_raw(f"[{THEME['border']}]{'═' * 70}[/]")
