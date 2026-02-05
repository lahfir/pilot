"""
Task history tracking for quick re-selection.
"""

from __future__ import annotations

from typing import List, Optional

from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich.console import Console

from ..theme import THEME
from .style import get_inquirer_style


_task_history: List[str] = []
_max_task_history = 10


def add_to_task_history(task: str) -> None:
    """
    Add a task to the history for quick re-selection.

    Args:
        task: Task description.
    """
    task = task.strip()
    if not task:
        return

    if task in _task_history:
        _task_history.remove(task)

    _task_history.insert(0, task)

    if len(_task_history) > _max_task_history:
        del _task_history[_max_task_history:]


def get_task_history() -> List[str]:
    """
    Get a copy of the current task history.

    Returns:
        List of recent tasks.
    """
    return _task_history.copy()


def select_from_task_history(console: Console) -> Optional[str]:
    """
    Show interactive task history selection with arrow keys.

    Args:
        console: Rich console.

    Returns:
        Selected task or None if cancelled/new task requested.
    """
    if not _task_history:
        console.print(f"  [{THEME['muted']}]No task history yet.[/]")
        return None

    choices = [
        Choice(value=task, name=task[:60] + "..." if len(task) > 60 else task)
        for task in _task_history
    ]
    choices.append(Choice(value=None, name="[Type new task...]"))

    try:
        selected = inquirer.select(
            message="Select recent task (or type new)",
            choices=choices,
            pointer="›",
            style=get_inquirer_style(),
            qmark="",
            amark="✓",
        ).execute()
        return selected
    except (EOFError, KeyboardInterrupt):
        return None
