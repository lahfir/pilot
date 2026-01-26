"""
Startup rendering helpers.
"""

from __future__ import annotations

from contextlib import contextmanager

from rich.console import Console

from ..state import VerbosityLevel
from ..theme import THEME


def print_hud_system_status(
    console: Console,
    capabilities,
    tool_count: int,
    webhook_port: int | None,
    browser_profile: str,
    verbosity: VerbosityLevel = VerbosityLevel.NORMAL,
) -> None:
    """
    Display comprehensive HUD system status.

    Args:
        console: Rich console.
        capabilities: Platform capabilities object.
        tool_count: Number of loaded tools.
        webhook_port: Webhook server port or None.
        browser_profile: Browser profile name.
        verbosity: Output verbosity.
    """
    if verbosity == VerbosityLevel.QUIET:
        return

    c_text = THEME["hud_text"]
    c_dim = THEME["hud_dim"]
    c_muted = THEME["hud_muted"]
    c_border = THEME["hud_border"]
    c_success = THEME["hud_active"]
    c_error = THEME["hud_error"]

    platform_str = f"{capabilities.os_type.title()} {capabilities.os_version}"
    display_str = (
        f"{capabilities.screen_resolution[0]}×{capabilities.screen_resolution[1]}"
    )
    acc_ok = capabilities.accessibility_api_available
    webhook_str = f":{webhook_port}" if webhook_port else "OFF"

    console.print()
    console.print(f"[{c_border}]╭─ [{c_dim}]SYSTEM STATUS[/] {'─' * 40}╮[/]")

    console.print(f"[{c_border}]│[/]  [{c_dim}]▸ PLATFORM[/]")
    console.print(
        f"[{c_border}]│[/]    [{c_muted}]OS[/]            [{c_text}]{platform_str}[/]"
    )
    console.print(
        f"[{c_border}]│[/]    [{c_muted}]DISPLAY[/]       [{c_text}]{display_str}[/]"
    )
    acc_status = f"[{c_success}]●[/] GRANTED" if acc_ok else f"[{c_error}]●[/] DENIED"
    console.print(f"[{c_border}]│[/]    [{c_muted}]ACCESSIBILITY[/] {acc_status}")

    console.print(f"[{c_border}]├{'─' * 55}┤[/]")
    console.print(f"[{c_border}]│[/]  [{c_dim}]▸ AGENTS[/]")
    console.print(
        f"[{c_border}]│[/]    [{c_text}]BROWSER[/]  [{c_dim}]web automation[/]   [{c_muted}]web_auto[/]"
    )
    console.print(
        f"[{c_border}]│[/]    [{c_text}]GUI[/]      [{c_dim}]desktop control[/]  [{c_muted}]click type read[/]"
    )
    console.print(
        f"[{c_border}]│[/]    [{c_text}]SYSTEM[/]   [{c_dim}]shell commands[/]   [{c_muted}]exec_shell[/]"
    )
    console.print(
        f"[{c_border}]│[/]    [{c_text}]CODE[/]     [{c_dim}]code generation[/]  [{c_muted}]code_auto[/]"
    )

    console.print(f"[{c_border}]├{'─' * 55}┤[/]")
    console.print(f"[{c_border}]│[/]  [{c_dim}]▸ SERVICES[/]")
    console.print(
        f"[{c_border}]│[/]    [{c_muted}]TOOLS[/]    [{c_success}]●[/] [{c_text}]{tool_count}[/]"
    )
    wh_status = f"[{c_success}]●[/]" if webhook_port else f"[{c_muted}]○[/]"
    console.print(
        f"[{c_border}]│[/]    [{c_muted}]WEBHOOK[/]  {wh_status} [{c_text}]{webhook_str}[/]"
    )
    console.print(
        f"[{c_border}]│[/]    [{c_muted}]BROWSER[/]  [{c_success}]●[/] [{c_text}]{browser_profile}[/]"
    )

    console.print(f"[{c_border}]├{'─' * 55}┤[/]")
    console.print(
        f"[{c_border}]│[/]  [{c_success}]●[/] [{c_text}]ONLINE[/]  "
        f"[{c_muted}]F5[/] [{c_dim}]voice[/]  "
        f"[{c_muted}]ESC[/] [{c_dim}]cancel[/]  "
        f"[{c_muted}]^C[/] [{c_dim}]quit[/]  "
        f"[{c_muted}]h[/] [{c_dim}]history[/]"
    )
    console.print(f"[{c_border}]╰{'─' * 55}╯[/]")
    console.print()


@contextmanager
def startup_spinner(console: Console, message: str):
    """
    Context manager for startup tasks with animated headset spinner.

    Uses the PILOT headset mascot with blinking ear cups.

    Args:
        console: Rich console.
        message: Spinner message.
    """
    from ..headset_loader import headset_spinner

    with headset_spinner(console, message, size="medium") as loader:
        yield loader
