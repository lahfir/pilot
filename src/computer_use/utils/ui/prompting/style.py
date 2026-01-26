"""
Shared styling and prompt session setup for interactive prompts.
"""

from __future__ import annotations

from typing import Dict

from InquirerPy.utils import InquirerPyStyle
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings

from ..theme import THEME


def get_inquirer_style() -> InquirerPyStyle:
    """
    Build and return the InquirerPy style used across prompts.

    Returns:
        InquirerPyStyle instance.
    """
    style_dict: Dict[str, str] = {
        "questionmark": THEME["warning"],
        "answermark": THEME["hud_success"],
        "answer": THEME["hud_active"],
        "input": THEME["hud_text"],
        "question": THEME["hud_text"],
        "answered_question": THEME["hud_muted"],
        "instruction": THEME["hud_muted"],
        "long_instruction": THEME["hud_muted"],
        "pointer": f"{THEME['hud_active']} bold",
        "checkbox": THEME["hud_success"],
        "separator": THEME["hud_border"],
        "skipped": THEME["hud_muted"],
        "validator": THEME["error"],
        "marker": THEME["warning"],
        "fuzzy_prompt": "#c678dd",
        "fuzzy_info": "#636d83",
        "fuzzy_border": "#4b5263",
        "fuzzy_match": "#c678dd",
        "spinner_pattern": "#c678dd",
        "spinner_text": "#abb2bf",
    }
    return InquirerPyStyle(style_dict)


def get_voice_mode_state() -> Dict[str, bool]:
    """
    Return the shared voice mode enabled state.

    Returns:
        A dict with a single 'value' boolean key.
    """
    return _voice_mode_enabled


def get_prompt_session() -> PromptSession:
    """
    Return the shared PromptSession instance.

    Returns:
        PromptSession configured for multiline input and keybindings.
    """
    return _prompt_session


_key_bindings = KeyBindings()
_voice_mode_enabled: Dict[str, bool] = {"value": False}


@_key_bindings.add("enter")
def _on_enter(event) -> None:
    """Handle Enter key submission."""
    event.current_buffer.validate_and_handle()


@_key_bindings.add("c-j")
def _on_ctrl_j(event) -> None:
    """Handle Ctrl+J insertion of a newline."""
    event.current_buffer.insert_text("\n")


@_key_bindings.add("escape", "enter")
def _on_alt_enter(event) -> None:
    """Handle Alt/Option+Enter insertion of a newline."""
    event.current_buffer.insert_text("\n")


@_key_bindings.add("f5")
def _on_f5(event) -> None:
    """Toggle voice input mode."""
    _voice_mode_enabled["value"] = not _voice_mode_enabled["value"]


_prompt_session = PromptSession(
    history=None,
    multiline=True,
    key_bindings=_key_bindings,
)
