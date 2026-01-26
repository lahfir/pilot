"""
Stable prompt API surface.

This module provides a backward-compatible interface for UI prompts and startup
rendering, delegating implementation to `computer_use.utils.ui.prompting`.
"""

from __future__ import annotations

import logging
from enum import Enum

from rich.console import Console

from .prompting import (
    add_to_task_history,
    get_task_history,
    get_task_input,
    get_voice_input,
    print_action_result_fn,
    print_banner,
    print_command_approval,
    print_failure,
    print_hud_system_status,
    print_info,
    print_success,
    print_task_result,
    print_verbose_only_fn,
    print_warning,
    prompt_human_assistance,
    select_from_task_history,
    startup_spinner,
)
from .state import VerbosityLevel

logger = logging.getLogger(__name__)


class HumanAssistanceResult(Enum):
    """Result of human assistance prompt."""

    PROCEED = "proceed"
    RETRY = "retry"
    SKIP = "skip"
    CANCEL = "cancel"


class CommandApprovalResult(Enum):
    """Result of command approval prompt."""

    ALLOW_ONCE = "1"
    ALLOW_SESSION = "2"
    DENY = "3"


def print_startup_step(console: Console, message: str, success: bool = True) -> None:
    """
    Print a startup step.

    This is a no-op because the dashboard HUD now owns step rendering.
    """
    _ = console, message, success


def print_platform_info(
    console: Console, capabilities, verbosity: VerbosityLevel = VerbosityLevel.NORMAL
) -> None:
    """
    Display platform info.

    This is a no-op because the dashboard HUD now owns platform rendering.
    """
    _ = console, capabilities, verbosity


def print_status_overview(console: Console, title: str, items: dict) -> None:
    """
    Display a status overview.

    This is a no-op because the dashboard HUD now owns status rendering.
    """
    _ = console, title, items


def print_ready(console: Console) -> None:
    """
    Print ready message.

    This is a no-op because the dashboard HUD now owns the ready state display.
    """
    _ = console


def format_duration(seconds: float) -> str:
    """
    Format duration for display.

    Args:
        seconds: Duration in seconds.

    Returns:
        Human-readable duration string.
    """
    from .formatters import format_duration as _format_duration

    return _format_duration(seconds)


__all__ = [
    "HumanAssistanceResult",
    "CommandApprovalResult",
    "print_banner",
    "print_startup_step",
    "print_platform_info",
    "print_status_overview",
    "print_ready",
    "print_hud_system_status",
    "startup_spinner",
    "get_task_input",
    "get_voice_input",
    "prompt_human_assistance",
    "print_command_approval",
    "print_task_result",
    "print_info",
    "print_success",
    "print_warning",
    "print_failure",
    "print_verbose_only_fn",
    "add_to_task_history",
    "get_task_history",
    "select_from_task_history",
    "print_action_result_fn",
    "format_duration",
]
