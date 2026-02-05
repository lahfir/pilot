"""
Task input flow for text and voice entry.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from prompt_toolkit.formatted_text import FormattedText
from rich.console import Console

from ..theme import THEME
from .style import get_prompt_session, get_voice_mode_state
from .voice import get_voice_input


def _print_hud_input_prompt(console: Console) -> None:
    """
    Print the HUD input prompt.

    Args:
        console: Rich console.
    """
    c_text = THEME["hud_text"]
    console.print(f"[{c_text}]What would you like me to do?[/]")


async def get_task_input(
    console: Console, start_with_voice: bool = False
) -> Optional[str]:
    """
    Get task input from user via text or voice with HUD-style prompt.

    Args:
        console: Rich console for output.
        start_with_voice: If True, start with voice input mode.

    Returns:
        User input text or None if cancelled.
    """
    voice_state = get_voice_mode_state()
    use_voice = start_with_voice or voice_state["value"]

    if use_voice:
        _print_hud_input_prompt(console)
        result = await get_voice_input(console)
        if result:
            voice_state["value"] = False
            return result
        console.print(f"  [{THEME['muted']}]Falling back to text input...[/]")

    try:
        _print_hud_input_prompt(console)
        loop = asyncio.get_event_loop()
        session = get_prompt_session()
        result = await loop.run_in_executor(
            None,
            lambda: session.prompt(
                FormattedText([(THEME["hud_active"], "▸ ")]),
                multiline=True,
            ),
        )
        return result.strip() if result else None
    except (EOFError, KeyboardInterrupt):
        return None
