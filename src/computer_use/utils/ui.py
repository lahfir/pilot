"""
Premium terminal UI - Claude-code style experience.
Beautiful, responsive, and informative.
"""

import asyncio
import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import box
from rich.rule import Rule
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from typing import Optional
from contextlib import contextmanager

console = Console()

THEME = {
    "primary": "#00d7ff",
    "secondary": "#ff79c6",
    "success": "#50fa7b",
    "warning": "#ffb86c",
    "error": "#ff5555",
    "info": "#8be9fd",
    "muted": "#6272a4",
    "accent": "#bd93f9",
}

_key_bindings = KeyBindings()
_voice_mode_enabled = {"value": False}


@_key_bindings.add("enter")
def _(event):
    """Handle Enter key - submit the input."""
    event.current_buffer.validate_and_handle()


@_key_bindings.add("c-j")
def _(event):
    """Handle Ctrl+J - insert newline."""
    event.current_buffer.insert_text("\n")


@_key_bindings.add("escape", "enter")
def _(event):
    """Handle Alt/Option+Enter - insert newline."""
    event.current_buffer.insert_text("\n")


@_key_bindings.add("f5")
def _(event):
    """Handle F5 - toggle voice input mode."""
    _voice_mode_enabled["value"] = not _voice_mode_enabled["value"]
    mode = "🎤 Voice" if _voice_mode_enabled["value"] else "⌨️  Text"
    console.print(f"\n[{THEME['info']}]Switched to {mode} mode[/]")


_prompt_session = PromptSession(
    history=None,
    multiline=True,
    key_bindings=_key_bindings,
)


def print_banner():
    """Display minimal, elegant startup banner."""
    console.print()

    title = Text()
    title.append("◆ ", style=f"bold {THEME['accent']}")
    title.append("Computer Use Agent", style=f"bold {THEME['primary']}")

    subtitle = Text()
    subtitle.append("  Autonomous Desktop & Web Automation", style=THEME["muted"])

    console.print(title)
    console.print(subtitle)
    console.print()

    hints = Text()
    hints.append("  ", style="")
    hints.append("F5", style=f"bold {THEME['info']}")
    hints.append(" voice  ", style=THEME["muted"])
    hints.append("Alt+↵", style=f"bold {THEME['info']}")
    hints.append(" newline  ", style=THEME["muted"])
    hints.append("Ctrl+C", style=f"bold {THEME['info']}")
    hints.append(" cancel", style=THEME["muted"])
    console.print(hints)
    console.print()


def print_section_header(title: str, icon: str = ""):
    """Print styled section header."""
    console.print()
    text = Text()
    if icon:
        text.append(f"{icon} ", style=THEME["accent"])
    text.append(title, style=f"bold {THEME['primary']}")
    console.print(text)
    console.print(Rule(style=THEME["muted"]))


def print_platform_info(capabilities):
    """Display platform capabilities in compact format."""
    console.print()

    main_table = Table(
        box=box.SIMPLE,
        show_header=False,
        padding=(0, 2),
        collapse_padding=True,
    )
    main_table.add_column("", style=THEME["muted"])
    main_table.add_column("", style="white")

    main_table.add_row(
        "Platform", f"{capabilities.os_type.title()} {capabilities.os_version}"
    )
    main_table.add_row(
        "Display",
        f"{capabilities.screen_resolution[0]}×{capabilities.screen_resolution[1]} @ {capabilities.scaling_factor}x",
    )

    if capabilities.gpu_available:
        gpu_text = f"✓ {capabilities.gpu_type}"
        main_table.add_row("GPU", f"[{THEME['success']}]{gpu_text}[/]")
    else:
        main_table.add_row("GPU", f"[{THEME['warning']}]CPU mode[/]")

    if capabilities.accessibility_api_available:
        acc_text = f"✓ {capabilities.accessibility_api_type}"
        main_table.add_row("Accessibility", f"[{THEME['success']}]{acc_text}[/]")
    else:
        main_table.add_row("Accessibility", f"[{THEME['warning']}]Not available[/]")

    console.print(main_table)
    console.print()


def print_agent_start(agent_name: str):
    """Announce agent execution with minimal style."""
    text = Text()
    text.append("▶ ", style=f"bold {THEME['accent']}")
    text.append(agent_name, style=f"bold {THEME['primary']}")
    text.append(" agent", style=THEME["muted"])
    console.print()
    console.print(text)


def print_step(step: int, action: str, target: str, reasoning: str):
    """Display agent step with clean formatting."""
    text = Text()
    text.append(f"  {step}. ", style=THEME["muted"])
    text.append(action, style=f"bold {THEME['info']}")
    text.append(" → ", style=THEME["muted"])
    text.append(target, style="white")
    console.print(text)

    if reasoning:
        console.print(f"     [{THEME['muted']}]{reasoning}[/]")


def print_success(message: str):
    """Print success message."""
    text = Text()
    text.append("  ✓ ", style=f"bold {THEME['success']}")
    text.append(message, style=THEME["success"])
    console.print(text)


def print_failure(message: str):
    """Print failure message."""
    text = Text()
    text.append("  ✗ ", style=f"bold {THEME['error']}")
    text.append(message, style=THEME["error"])
    console.print(text)


def print_info(message: str):
    """Print info message."""
    text = Text()
    text.append("  ℹ ", style=f"bold {THEME['info']}")
    text.append(message, style=THEME["info"])
    console.print(text)


def print_warning(message: str):
    """Print warning message."""
    text = Text()
    text.append("  ⚠ ", style=f"bold {THEME['warning']}")
    text.append(message, style=THEME["warning"])
    console.print(text)


@contextmanager
def action_spinner(action: str, target: str):
    """
    Context manager that shows a spinner during an action.
    The spinner disappears when the action completes.

    Args:
        action: Action being performed (e.g., "Clicking", "Typing")
        target: Target of the action

    Example:
        with action_spinner("Clicking", "Submit button"):
            perform_click()
        # Spinner automatically disappears
    """
    status_text = Text()
    status_text.append(f"  ● {action} ", style=f"bold {THEME['info']}")
    status_text.append(f"'{target}'", style=THEME["warning"])

    spinner = Spinner("dots", text=status_text)

    try:
        with Live(spinner, console=console, refresh_per_second=12, transient=True):
            yield
    except Exception:
        raise


@contextmanager
def task_progress(title: str, total: int = 0):
    """
    Context manager for multi-step task progress.

    Args:
        title: Progress title
        total: Total steps (0 for indeterminate)
    """
    progress = Progress(
        SpinnerColumn(),
        TextColumn(f"[{THEME['info']}]{title}[/]"),
        BarColumn(complete_style=THEME["success"], finished_style=THEME["success"]),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
        transient=True,
    )

    with progress:
        task_id = progress.add_task(title, total=total or 100)

        class ProgressUpdater:
            def advance(self, amount: int = 1):
                progress.advance(task_id, amount)

            def complete(self):
                progress.update(task_id, completed=total or 100)

        yield ProgressUpdater()


def print_action(action: str, target: str, detail: Optional[str] = None):
    """
    Print action being taken (non-blocking, instant display).

    Args:
        action: Action verb (Clicking, Typing, etc.)
        target: Target element
        detail: Optional detail
    """
    text = Text()
    text.append("  → ", style=f"bold {THEME['accent']}")
    text.append(f"{action} ", style=f"bold {THEME['info']}")
    text.append(f"'{target}'", style=THEME["warning"])
    if detail:
        text.append(f" ({detail})", style=THEME["muted"])
    console.print(text)


def print_action_result(success: bool, message: str):
    """
    Print action result on same line concept.

    Args:
        success: Whether action succeeded
        message: Result message
    """
    if success:
        text = Text()
        text.append("    ✓ ", style=f"bold {THEME['success']}")
        text.append(message, style=THEME["muted"])
        console.print(text)
    else:
        text = Text()
        text.append("    ✗ ", style=f"bold {THEME['error']}")
        text.append(message, style=THEME["muted"])
        console.print(text)


def print_command_approval(command: str) -> str:
    """Display command approval request with clean design."""
    console.print()

    panel_content = Text()
    panel_content.append("Command: ", style=f"bold {THEME['warning']}")
    panel_content.append(command, style="white")
    panel_content.append("\n\n")
    panel_content.append("1", style=f"bold {THEME['success']}")
    panel_content.append(" Allow once  ", style="white")
    panel_content.append("2", style=f"bold {THEME['info']}")
    panel_content.append(" Allow session  ", style="white")
    panel_content.append("3", style=f"bold {THEME['error']}")
    panel_content.append(" Deny", style="white")

    panel = Panel(
        panel_content,
        title=f"[{THEME['warning']}]🔐 Approval Required[/]",
        border_style=THEME["warning"],
        box=box.ROUNDED,
        padding=(1, 2),
    )
    console.print(panel)

    choice = console.input("[bold]Choice (1/2/3):[/] ").strip()
    return choice


def print_handoff(from_agent: str, to_agent: str, reason: str):
    """Display agent handoff with minimal style."""
    console.print()
    text = Text()
    text.append("  ↪ ", style=f"bold {THEME['accent']}")
    text.append(from_agent, style=THEME["info"])
    text.append(" → ", style=THEME["muted"])
    text.append(to_agent, style=THEME["info"])
    if reason:
        text.append(f" ({reason})", style=THEME["muted"])
    console.print(text)


def print_task_result(result):
    """Display final task result with clean formatting."""
    console.print()

    if hasattr(result, "overall_success"):
        success = result.overall_success
        result_text = getattr(result, "result", None)
        error = getattr(result, "error", None)
    else:
        success = result.get("overall_success", False)
        result_text = result.get("result")
        error = result.get("error")

    if success:
        header = Text()
        header.append("✓ ", style=f"bold {THEME['success']}")
        header.append("Complete", style=f"bold {THEME['success']}")
        console.print(header)
    else:
        header = Text()
        header.append("✗ ", style=f"bold {THEME['error']}")
        header.append("Failed", style=f"bold {THEME['error']}")
        console.print(header)
        if error:
            console.print(f"  [{THEME['error']}]{error}[/]")

    if result_text and isinstance(result_text, str):
        console.print()
        shortened = result_text[:500] + "..." if len(result_text) > 500 else result_text
        console.print(f"  [{THEME['muted']}]{shortened}[/]")

    console.print()


def print_action_history(history: list):
    """Display action history in compact format."""
    if not history:
        return

    console.print()
    console.print(f"  [{THEME['muted']}]Recent actions:[/]")

    for action in history[-5:]:
        status = "✓" if action.get("success") else "✗"
        style = THEME["success"] if action.get("success") else THEME["error"]
        console.print(
            f"    [{style}]{status}[/] {action.get('action', '')} → {action.get('target', '')[:30]}"
        )


def print_webhook_status(port: int, status: str = "starting"):
    """Display webhook server status."""
    if status == "starting":
        console.print(f"  [{THEME['info']}]Starting webhook on port {port}...[/]")
    elif status == "ready":
        console.print(f"  [{THEME['success']}]✓ Webhook ready on port {port}[/]")
    elif status == "port_changed":
        console.print(f"  [{THEME['warning']}]Port {port - 1} in use, trying {port}[/]")
    elif status == "failed":
        console.print(
            f"  [{THEME['error']}]✗ Could not start webhook on port {port}[/]"
        )


def print_twilio_config_status(is_configured: bool, phone_number: str = None):
    """Display Twilio configuration status."""
    if is_configured and phone_number:
        console.print(f"  [{THEME['success']}]✓ Twilio: {phone_number}[/]")
    else:
        console.print(f"  [{THEME['warning']}]Twilio not configured[/]")


def print_element_found(element_type: str, label: str, coords: Optional[tuple] = None):
    """
    Print element found notification.

    Args:
        element_type: Type of element
        label: Element label
        coords: Optional (x, y) coordinates
    """
    text = Text()
    text.append("    ◎ ", style=THEME["accent"])
    text.append(f"Found {element_type} ", style=THEME["muted"])
    text.append(f"'{label}'", style="white")
    if coords:
        text.append(f" at ({coords[0]}, {coords[1]})", style=THEME["muted"])
    console.print(text)


def print_thinking(message: str = "Analyzing..."):
    """
    Print thinking/analyzing indicator.

    Args:
        message: Thinking message
    """
    text = Text()
    text.append("  ◌ ", style=f"bold {THEME['accent']}")
    text.append(message, style=THEME["muted"])
    console.print(text)


async def get_voice_input() -> Optional[str]:
    """Capture voice input using Deepgram streaming API."""
    try:
        from ..services.voice_input_service import VoiceInputService
        from ..services.audio_capture import AudioCapture

        if not VoiceInputService.check_api_key_configured():
            print_failure("DEEPGRAM_API_KEY not found")
            return None

        if not AudioCapture.check_microphone_available():
            print_failure("No microphone detected")
            return None

        console.print()
        console.print(
            f"  [{THEME['success']}]🎤 Listening...[/] [{THEME['muted']}](Enter to finish)[/]"
        )

        max_width = console.width - 10

        def on_interim(text: str) -> None:
            display_text = text[:max_width] if len(text) > max_width else text
            padding = " " * max(0, max_width - len(display_text))
            sys.stdout.write(f"\r  [{THEME['info']}]▸ {display_text}[/]{padding}")
            sys.stdout.flush()

        voice_service = VoiceInputService()
        language = os.getenv("VOICE_INPUT_LANGUAGE", "multi")
        started = await voice_service.start_transcription(
            interim_callback=on_interim, language=language
        )

        if not started:
            print_failure(f"Voice input failed: {voice_service.get_error()}")
            return None

        await asyncio.sleep(0.5)

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, input)
        except (KeyboardInterrupt, EOFError):
            pass

        result = await voice_service.stop_transcription()
        sys.stdout.write("\n")
        sys.stdout.flush()

        if result:
            print_success(f"Transcribed: {result}")
        else:
            print_warning("No speech detected")

        return result.strip() if result else None

    except ImportError as e:
        print_failure(f"Voice dependencies missing: {e}")
        return None
    except Exception as e:
        print_failure(f"Voice input error: {e}")
        return None


async def get_task_input(start_with_voice: bool = False) -> str:
    """
    Get task input with support for text and voice modes.

    Args:
        start_with_voice: Start in voice mode

    Returns:
        User's task input
    """
    global _voice_mode_enabled
    _voice_mode_enabled["value"] = start_with_voice

    try:
        while True:
            if _voice_mode_enabled["value"]:
                result = await get_voice_input()
                if result:
                    return result
                _voice_mode_enabled["value"] = False
                continue

            console.print()
            mode = "voice" if _voice_mode_enabled["value"] else "text"
            console.print(
                f"[{THEME['primary']}]What would you like me to do?[/] [{THEME['muted']}]({mode} mode)[/]"
            )

            prompt_text = FormattedText([(THEME["primary"], "❯ ")])

            task = await _prompt_session.prompt_async(
                prompt_text,
                prompt_continuation=FormattedText([("", "  ")]),
            )

            return task.strip()
    except (KeyboardInterrupt, EOFError):
        return "quit"
