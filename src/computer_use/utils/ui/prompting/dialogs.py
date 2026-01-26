"""
Interactive dialogs for approvals and human assistance.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich.console import Console

from ..theme import THEME
from .style import get_inquirer_style

if TYPE_CHECKING:
    pass


def prompt_human_assistance(
    console: Console, reason: str, instructions: str, result_enum
):
    """
    Display a human assistance dialog with arrow-key selection menu.

    Args:
        console: Rich console.
        reason: A short reason for requesting assistance.
        instructions: What the user should do.
        result_enum: Enum type mapping for the result.

    Returns:
        An enum value from result_enum.
    """
    console.print()
    console.print(f"[bold {THEME['warning']}]{'─' * 50}[/]")
    console.print(f"[bold {THEME['warning']}]🤝 HUMAN ASSISTANCE REQUIRED[/]")
    console.print()

    if reason:
        console.print(f"[{THEME['muted']}]Reason:[/] {reason}")
    if instructions:
        console.print(f"[{THEME['muted']}]Instructions:[/] {instructions}")

    console.print(f"[bold {THEME['warning']}]{'─' * 50}[/]")
    console.print()

    try:
        choice = inquirer.select(
            message="Select action",
            choices=[
                Choice(value="proceed", name="Proceed - Continue with the task"),
                Choice(value="retry", name="Retry - Try again with different approach"),
                Choice(value="skip", name="Skip - Skip this step"),
                Choice(value="cancel", name="Cancel - Stop the entire task"),
            ],
            default="proceed",
            pointer="›",
            style=get_inquirer_style(),
            qmark="",
            amark="✓",
        ).execute()
    except (EOFError, KeyboardInterrupt):
        return result_enum.CANCEL

    result_map = {
        "proceed": result_enum.PROCEED,
        "retry": result_enum.RETRY,
        "skip": result_enum.SKIP,
        "cancel": result_enum.CANCEL,
    }
    return result_map.get(choice, result_enum.CANCEL)


def print_command_approval(
    console: Console,
    command: str,
    deny_value: str,
    allow_once_value: str,
    allow_session_value: str,
) -> str:
    """
    Display command approval dialog with arrow-key selection menu.

    Args:
        console: Rich console.
        command: Command string being approved.
        deny_value: Value returned for denial.
        allow_once_value: Value returned for allow once.
        allow_session_value: Value returned for allow for session.

    Returns:
        Selected value string.
    """
    from ..dashboard import dashboard

    dashboard._stop_live_status()

    c_border = THEME["hud_border"]
    c_warning = THEME["warning"]
    c_text = THEME["hud_text"]
    c_muted = THEME["hud_muted"]

    console.print()
    console.print(f"[{c_border}]╭{'─' * 50}╮[/]")
    console.print(f"[{c_border}]│[/] [{c_warning}]⚠ COMMAND REQUIRES APPROVAL[/]")
    console.print(f"[{c_border}]├{'─' * 50}┤[/]")
    console.print(f"[{c_border}]│[/] [{c_muted}]Command:[/]")
    console.print(f"[{c_border}]│[/]   [{c_text}]{command}[/]")
    console.print(f"[{c_border}]╰{'─' * 50}╯[/]")
    console.print()

    try:
        choice = inquirer.select(
            message="",
            choices=[
                Choice(value=allow_once_value, name="Allow once"),
                Choice(value=allow_session_value, name="Allow for session"),
                Choice(value=deny_value, name="Deny & stop"),
            ],
            default=allow_once_value,
            pointer="›",
            style=get_inquirer_style(),
            qmark="",
            amark="✓",
        ).execute()
        dashboard._start_live_status()
        return choice or deny_value
    except (EOFError, KeyboardInterrupt):
        dashboard._start_live_status()
        return deny_value
