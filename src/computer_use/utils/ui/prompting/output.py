"""
Output helpers for user-facing UI messages.
"""

from __future__ import annotations

from contextlib import contextmanager

from rich.console import Console

from ..state import ActionType
from ..theme import ICONS, THEME


@contextmanager
def action_spinner_ctx(console: Console, action: str, target: str = ""):
    """
    Context manager for actions with dashboard-backed status.

    Args:
        console: Rich console.
        action: Action label.
        target: Optional target label.
    """
    from ..dashboard import dashboard

    _ = console
    if dashboard.is_quiet:
        yield
        return

    display = f"{action} {target}".strip()
    idx = dashboard.add_log_entry(ActionType.EXECUTE, display)
    dashboard.set_action(action, target if target else None)

    try:
        yield
        dashboard.update_log_entry(idx, "complete")
    except Exception:
        dashboard.update_log_entry(idx, "error")
        raise
    finally:
        dashboard.clear_action()


def print_action_result_fn(console: Console, success: bool, message: str) -> None:
    """
    Print the result of an action.

    Args:
        console: Rich console.
        success: Whether the action succeeded.
        message: Message to print.
    """
    from ..dashboard import dashboard

    _ = console
    if dashboard.is_quiet:
        return

    if success:
        dashboard.console.print(
            f"  [{THEME['tool_success']}]{ICONS['success']}[/] {message}"
        )
    else:
        dashboard.console.print(f"  [{THEME['error']}]{ICONS['error']}[/] {message}")


def print_verbose_only_fn(console: Console, message: str) -> None:
    """
    Print message only in verbose mode.

    Args:
        console: Rich console.
        message: Message to print.
    """
    from ..dashboard import dashboard

    _ = console
    if dashboard.is_verbose:
        dashboard.console.print(f"  {message}")


def print_info(console: Console, message: str) -> None:
    """
    Print an info message.

    Args:
        console: Rich console.
        message: Message to print.
    """
    console.print(f"  [{THEME['text']}]ℹ[/] {message}")


def print_success(console: Console, message: str) -> None:
    """
    Print a success message.

    Args:
        console: Rich console.
        message: Message to print.
    """
    console.print(f"  [{THEME['tool_success']}]{ICONS['success']}[/] {message}")


def print_warning(console: Console, message: str) -> None:
    """
    Print a warning message.

    Args:
        console: Rich console.
        message: Message to print.
    """
    console.print(f"  [{THEME['warning']}]{ICONS['warning']}[/] {message}")


def print_failure(console: Console, message: str) -> None:
    """
    Print a failure message.

    Args:
        console: Rich console.
        message: Message to print.
    """
    console.print(f"  [{THEME['error']}]{ICONS['error']}[/] {message}")
