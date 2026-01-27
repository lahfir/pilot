"""
Voice input capture for task entry.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from rich.console import Console

from ..headset_loader import HeadsetLoader
from ..theme import THEME

logger = logging.getLogger(__name__)


async def get_voice_input(console: Console) -> Optional[str]:
    """
    Capture voice input using the VoiceInputService.

    Args:
        console: Rich console.

    Returns:
        Transcribed text or None if voice input failed or was cancelled.
    """
    try:
        from computer_use.services.voice_input_service import VoiceInputService
        from computer_use.services.audio_capture import AudioCapture
    except ImportError as e:
        logger.error(f"Voice input dependencies not available: {e}")
        console.print(
            f"  [{THEME['error']}]Voice input unavailable: missing dependencies[/]"
        )
        return None

    if not VoiceInputService.check_api_key_configured():
        console.print(f"  [{THEME['warning']}]Voice input requires DEEPGRAM_API_KEY[/]")
        return None

    if not AudioCapture.check_microphone_available():
        console.print(f"  [{THEME['warning']}]No microphone available[/]")
        return None

    try:
        service = VoiceInputService()
    except ValueError as e:
        console.print(f"  [{THEME['error']}]Voice service error: {e}[/]")
        return None

    interim_text = {"value": ""}
    loader_ref = {"ref": None}

    def on_interim(text: str) -> None:
        """Update the interim transcription display."""
        interim_text["value"] = text
        if loader_ref["ref"]:
            loader_ref["ref"].set_message(f"🎤 {text}")

    console.print(
        f"  [{THEME['tool_pending']}]🎤 Listening... (press Enter to stop)[/]"
    )

    loader = HeadsetLoader(
        console=console,
        message="Waiting for speech...",
        size="mini",
        centered=False,
    )
    loader_ref["ref"] = loader
    loader.start()

    success = await service.start_transcription(interim_callback=on_interim)

    if not success:
        loader.stop()
        error = service.get_error()
        console.print(f"  [{THEME['error']}]Failed to start voice input: {error}[/]")
        return None

    loop = asyncio.get_event_loop()
    stop_event = asyncio.Event()

    def wait_for_enter() -> None:
        """Wait for Enter key in a thread."""
        try:
            input()
            loop.call_soon_threadsafe(stop_event.set)
        except (EOFError, KeyboardInterrupt):
            loop.call_soon_threadsafe(stop_event.set)

    loop.run_in_executor(None, wait_for_enter)

    await stop_event.wait()

    loader.stop()
    result = await service.stop_transcription()

    if result:
        console.print(f"  [{THEME['tool_success']}]✓[/] [{THEME['text']}]{result}[/]")
    else:
        console.print(f"  [{THEME['muted']}]No speech detected[/]")

    return result if result else None
