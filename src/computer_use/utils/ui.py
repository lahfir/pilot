"""
Professional terminal UI using rich and prompt_toolkit.
"""

import asyncio
import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from typing import Optional

console = Console()

_key_bindings = KeyBindings()
_voice_mode_enabled = {"value": False}


@_key_bindings.add("enter")
def _(event):
    """
    Handle Enter key - submit the input.
    """
    event.current_buffer.validate_and_handle()


@_key_bindings.add("c-j")
def _(event):
    """
    Handle Ctrl+J - insert newline (alternative for Shift+Enter).
    """
    event.current_buffer.insert_text("\n")


@_key_bindings.add("escape", "enter")
def _(event):
    """
    Handle Alt/Option+Enter - insert newline.
    """
    event.current_buffer.insert_text("\n")


@_key_bindings.add("f5")
def _(event):
    """
    Handle F5 - toggle voice input mode.
    """
    _voice_mode_enabled["value"] = not _voice_mode_enabled["value"]
    mode = "🎤 Voice" if _voice_mode_enabled["value"] else "⌨️  Text"
    console.print(f"\n[cyan]Switched to {mode} input mode (F5)[/cyan]")


_prompt_session = PromptSession(
    history=None,
    multiline=True,
    key_bindings=_key_bindings,
)


def print_banner():
    """
    Display startup banner with voice input information.
    """
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║        🤖 Computer Use Agent - Multi-Platform             ║
    ║        Autonomous Desktop & Web Automation                ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")
    console.print()
    console.print(
        "[dim]💡 Input modes: Press [cyan]F5[/cyan] to toggle "
        "between ⌨️  text and 🎤 voice[/dim]"
    )
    voice_lang = os.getenv("VOICE_INPUT_LANGUAGE", "multi")
    if voice_lang == "multi":
        console.print("[dim]   Voice input: multilingual mode (100+ languages)[/dim]")
    else:
        console.print(
            f"[dim]   Voice input language: {voice_lang.upper()} "
            f"(set VOICE_INPUT_LANGUAGE=multi for multilingual)[/dim]"
        )


def print_section_header(title: str, icon: str = ""):
    """
    Print styled section header.
    """
    console.print()
    console.rule(f"{icon} {title}", style="bold blue")
    console.print()


def print_platform_info(capabilities):
    """
    Display platform capabilities in styled table.
    """
    table = Table(title="Platform Information", box=box.ROUNDED, show_header=False)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("OS", f"{capabilities.os_type} {capabilities.os_version}")
    table.add_row(
        "Screen",
        f"{capabilities.screen_resolution[0]}x{capabilities.screen_resolution[1]}",
    )
    table.add_row("Scaling", f"{capabilities.scaling_factor}x")

    if capabilities.gpu_available:
        gpu_info = (
            f"{capabilities.gpu_type} ({capabilities.gpu_device_count} device(s))"
        )
        table.add_row("GPU", f"✅ {gpu_info}")
    else:
        table.add_row("GPU", "⚠️  Not available (CPU only)")

    console.print(table)
    console.print()

    caps_table = Table(
        title="Automation Capabilities", box=box.ROUNDED, show_header=False
    )
    caps_table.add_column("Tier", style="cyan")
    caps_table.add_column("Status", style="white")

    if capabilities.accessibility_api_available:
        caps_table.add_row(
            "Tier 1",
            f"✅ {capabilities.accessibility_api_type} (100% accuracy)",
        )
    else:
        caps_table.add_row("Tier 1", "⚠️  Accessibility API not available")

    caps_table.add_row("Tier 2", "✅ Computer Vision + OCR (95-99% accuracy)")
    caps_table.add_row("Tier 3", "✅ Vision Model Fallback (85-95% accuracy)")

    console.print(caps_table)
    console.print()

    tools_list = " • ".join(capabilities.supported_tools)
    tools_table = Table(
        title="Available Tools", box=box.ROUNDED, show_header=False, width=80
    )
    tools_table.add_column("Tools", style="cyan", no_wrap=False)
    tools_table.add_row(tools_list)

    console.print(tools_table)


def print_agent_start(agent_name: str):
    """
    Announce agent execution start.
    """
    console.print()
    console.print(
        Panel(
            f"[bold cyan]{agent_name} Agent Executing[/bold cyan]",
            border_style="cyan",
            box=box.HEAVY,
        )
    )
    console.print()


def print_step(step: int, action: str, target: str, reasoning: str):
    """
    Display agent step with styling.
    """
    console.print(
        f"[bold blue]Step {step}:[/bold blue] [cyan]{action}[/cyan] → [white]{target}[/white]"
    )
    console.print(f"  [dim]{reasoning}[/dim]")


def print_success(message: str):
    """
    Print success message.
    """
    console.print(f"  [green]✅ {message}[/green]")


def print_failure(message: str):
    """
    Print failure message.
    """
    console.print(f"  [red]❌ {message}[/red]")


def print_info(message: str):
    """
    Print info message.
    """
    console.print(f"  [cyan]ℹ️  {message}[/cyan]")


def print_warning(message: str):
    """
    Print warning message.
    """
    console.print(f"  [yellow]⚠️  {message}[/yellow]")


def print_command_approval(command: str) -> str:
    """
    Display command approval request.

    Returns:
        User's choice ('1', '2', or '3')
    """
    console.print()
    panel = Panel(
        f"[bold yellow]💻 Command:[/bold yellow] [cyan]{command}[/cyan]\n\n"
        "[bold]Options:[/bold]\n"
        "  [green][1][/green] Allow once\n"
        "  [blue][2][/blue] Allow for session\n"
        "  [red][3][/red] Deny (stop agent)",
        title="🔐 Command Approval Required",
        border_style="yellow",
        box=box.DOUBLE,
    )
    console.print(panel)

    choice = console.input("[bold]Your choice (1/2/3):[/bold] ").strip()
    return choice


def print_handoff(from_agent: str, to_agent: str, reason: str):
    """
    Display agent handoff.
    """
    console.print()
    console.print(
        Panel(
            f"[bold]{from_agent}[/bold] → [bold]{to_agent}[/bold]\n\n"
            f"[dim]Reason: {reason}[/dim]",
            title="🤝 Agent Handoff",
            border_style="magenta",
            box=box.HEAVY,
        )
    )
    console.print()


def print_task_result(result):
    """
    Display final task result.
    Handles both dict and TaskExecutionResult objects.
    """
    console.print()

    if hasattr(result, "overall_success"):
        success = result.overall_success
        task = result.task
    else:
        success = result.get("overall_success", False)
        task = result.get("task", "Unknown")

    title = "✅ Task Complete" if success else "❌ Task Failed"
    style = "green" if success else "red"

    content = f"[bold]Task:[/bold] {task}\n\n"

    handoffs = []
    outputs = []

    results_list = None
    if hasattr(result, "results"):
        results_list = result.results
    elif isinstance(result, dict):
        results_list = result.get("results")

    if results_list:
        content += "[bold]Execution Steps:[/bold]\n\n"
        for i, res in enumerate(results_list, 1):
            if not res or not isinstance(res, dict):
                continue

            status = "✅" if res.get("success") else "❌"
            method = res.get("method_used", "unknown")
            action = res.get("action_taken", "")

            content += f"  {status} [cyan]Step {i}:[/cyan] [{method}] {action}\n"

            if res.get("error"):
                content += f"     [red]Error: {res['error']}[/red]\n"

            data = res.get("data")
            if data and isinstance(data, dict) and data.get("output"):
                outputs.append({"step": i, "method": method, "output": data["output"]})

            if res.get("handoff_requested"):
                handoffs.append(
                    {
                        "from": "GUI" if "gui" in method.lower() else "SYSTEM",
                        "to": res.get("suggested_agent", "unknown").upper(),
                        "reason": res.get("handoff_reason", ""),
                    }
                )

    if handoffs:
        content += "\n[bold magenta]Agent Handoffs:[/bold magenta]\n\n"
        for handoff in handoffs:
            content += f"  🤝 [cyan]{handoff['from']}[/cyan] → [yellow]{handoff['to']}[/yellow]\n"
            if handoff["reason"]:
                content += f"     [dim]Reason: {handoff['reason']}[/dim]\n"

    if outputs:
        content += "\n[bold green]📄 Results:[/bold green]\n\n"
        for output in outputs:
            content += f"[cyan]{output['method'].upper()}:[/cyan]\n"
            content += f"{output['output']}\n\n"

    panel = Panel(
        content,
        title=title,
        border_style=style,
        box=box.DOUBLE,
    )
    console.print(panel)


def print_action_history(history: list):
    """
    Display action history table.
    """
    if not history:
        return

    table = Table(title="📋 Action History", box=box.ROUNDED)
    table.add_column("#", style="cyan", width=4)
    table.add_column("Action", style="white")
    table.add_column("Target", style="yellow")
    table.add_column("Result", style="green")

    for i, action in enumerate(history[-5:], 1):  # Show last 5
        status = "✅" if action.get("success") else "❌"
        table.add_row(
            str(i),
            action.get("action", ""),
            action.get("target", "")[:30],
            status,
        )

    console.print(table)


def print_webhook_status(port: int, status: str = "starting"):
    """
    Display webhook server status with styled panel.

    Args:
        port: Port number the webhook is using
        status: Status of webhook ('starting', 'ready', 'failed', 'port_changed')
    """
    if status == "starting":
        console.print(
            f"[cyan]🌐 Twilio webhook server starting on port {port}...[/cyan]"
        )
    elif status == "ready":
        table = Table(
            title="📞 Twilio Webhook Server", box=box.ROUNDED, show_header=False
        )
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Status", "[green]✅ Ready[/green]")
        table.add_row("Local URL", f"http://localhost:{port}/sms")
        table.add_row("Health Check", f"http://localhost:{port}/health")
        table.add_row("Ngrok Command", f"[yellow]ngrok http {port}[/yellow]")

        console.print(table)
    elif status == "port_changed":
        console.print(
            f"[yellow]⚠️  Port {port - 1} in use, trying port {port}...[/yellow]"
        )
    elif status == "failed":
        console.print(f"[red]❌ Could not start webhook server on port {port}[/red]")


def print_twilio_config_status(is_configured: bool, phone_number: str = None):
    """
    Display Twilio configuration status.

    Args:
        is_configured: Whether Twilio is configured
        phone_number: Twilio phone number if configured
    """
    if is_configured and phone_number:
        console.print(
            f"[green]✅ Twilio configured with number: {phone_number}[/green]"
        )
    elif not is_configured:
        console.print(
            "[yellow]⚠️  Twilio not configured (phone verification unavailable)[/yellow]"
        )
        console.print(
            "[dim]   Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER in .env[/dim]"
        )


async def get_voice_input() -> Optional[str]:
    """
    Capture voice input using Deepgram streaming API.
    Shows real-time transcription feedback and returns final text.

    Returns:
        Transcribed text or None if cancelled/error
    """
    try:
        from ..services.voice_input_service import VoiceInputService
        from ..services.audio_capture import AudioCapture

        if not VoiceInputService.check_api_key_configured():
            console.print("[red]❌ DEEPGRAM_API_KEY not found in environment[/red]")
            console.print(
                "[yellow]Please set DEEPGRAM_API_KEY to use voice input[/yellow]"
            )
            return None

        if not AudioCapture.check_microphone_available():
            console.print("[red]❌ No microphone detected[/red]")
            return None

        language = os.getenv("VOICE_INPUT_LANGUAGE", "multi")

        console.print()
        console.print(
            "[bold green]🎤 Listening...[/bold green] "
            "[dim](Press Enter to finish, Ctrl+C to cancel)[/dim]"
        )
        if language == "multi":
            console.print(
                "[dim]Using multilingual mode - supports 100+ languages automatically[/dim]"
            )
        else:
            console.print(f"[dim]Language: {language.upper()}[/dim]")
        console.print()

        interim_text = {"value": ""}
        max_width = console.width - 10

        def on_interim(text: str) -> None:
            """Update interim transcription display on a single line."""
            interim_text["value"] = text
            display_text = text[:max_width] if len(text) > max_width else text
            padding = " " * max(0, max_width - len(display_text))
            sys.stdout.write(f"\r\033[36m➤ {display_text}\033[0m{padding}")
            sys.stdout.flush()

        voice_service = VoiceInputService()
        language = os.getenv("VOICE_INPUT_LANGUAGE", "multi")
        started = await voice_service.start_transcription(
            interim_callback=on_interim, language=language
        )

        if not started:
            error = voice_service.get_error()
            console.print(f"\n[red]❌ Failed to start voice input: {error}[/red]")
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
            console.print(f"[green]✅ Transcribed:[/green] {result}")
            if (
                voice_service.detected_language
                and voice_service.detected_language != "multi"
            ):
                console.print(
                    f"[dim]Language mode: {voice_service.detected_language}[/dim]"
                )
        else:
            console.print("[yellow]⚠️  No speech detected[/yellow]")

        return result.strip() if result else None

    except ImportError as e:
        console.print(f"[red]❌ Voice input dependencies not installed: {e}[/red]")
        console.print("[yellow]Run: pip install deepgram-sdk sounddevice[/yellow]")
        return None
    except Exception as e:
        console.print(f"[red]❌ Voice input error: {e}[/red]")
        return None


async def get_task_input(start_with_voice: bool = False) -> str:
    """
    Get task input from user with support for text and voice modes.
    Uses prompt_toolkit for text input with readline-like editing.
    Supports multi-line input via Alt+Enter or Ctrl+J.
    Toggle voice mode with Ctrl+V or F5.

    Args:
        start_with_voice: Start in voice mode if True

    Returns:
        User's task input (stripped)
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
            mode_indicator = (
                "⌨️  Text" if not _voice_mode_enabled["value"] else "🎤 Voice"
            )
            console.print(
                f"[#00d7ff]💬 Enter your task ([cyan]{mode_indicator}[/cyan] mode):[/]"
            )
            console.print(
                "[dim]   [cyan]F5[/cyan]: Toggle voice | "
                "[cyan]Alt+Enter[/cyan]: New line | [cyan]Enter[/cyan]: Submit[/dim]"
            )
            console.print()

            prompt_text = FormattedText([("#00d7ff bold", "➤ ")])

            task = await _prompt_session.prompt_async(
                prompt_text,
                prompt_continuation=FormattedText([("", "  ")]),
            )

            return task.strip()
    except (KeyboardInterrupt, EOFError):
        return "quit"
