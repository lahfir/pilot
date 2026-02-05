"""
Final task result formatting for display.
"""

from __future__ import annotations

from rich.console import Console

from ..theme import ICONS, THEME


def print_task_result(console: Console, result) -> None:
    """
    Display the final task result with readable formatting.

    Args:
        console: Rich console.
        result: Crew execution result-like object.
    """
    from rich.markdown import Markdown
    from rich.padding import Padding

    console.print()

    success = (hasattr(result, "overall_success") and result.overall_success) or (
        hasattr(result, "task_completed") and result.task_completed
    )

    if success:
        console.print(f"[bold {THEME['tool_success']}]{ICONS['success']} Complete[/]")
        console.print()

        if hasattr(result, "result") and result.result:
            md = Markdown(result.result)
            console.print(Padding(md, (0, 2)))

        if hasattr(result, "final_value") and result.final_value:
            console.print()
            console.print(f"  [{THEME['text']}]Result: {result.final_value}[/]")
    else:
        console.print(f"[bold {THEME['error']}]{ICONS['error']} Failed[/]")

        if hasattr(result, "error") and result.error:
            console.print(f"  [{THEME['error']}]{result.error}[/]")

    console.print()
