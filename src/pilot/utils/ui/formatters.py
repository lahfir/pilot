"""
Data formatting utilities for the UI.
"""

import json
from typing import Any, Dict, Tuple
from rich.text import Text
from rich.syntax import Syntax
from .theme import THEME


def format_duration(seconds: float) -> str:
    """
    Format a duration for display.

    Args:
        seconds: Duration in seconds

    Returns:
        Human-readable duration string
    """
    if seconds < 1:
        return f"{int(seconds * 1000)}ms"
    if seconds < 60:
        return f"{seconds:.1f}s"
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}m {secs}s"


def format_duration_hud(seconds: float) -> str:
    """
    Format a duration in HUD style.

    Args:
        seconds: Duration in seconds

    Returns:
        HUD-style duration string
    """
    if seconds < 0.01:
        return "0.01s"
    if seconds < 1:
        return f"{seconds:.2f}s"
    if seconds < 60:
        return f"{seconds:.1f}s"
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}m{secs:02d}s"


def format_duration_status(seconds: float) -> str:
    """
    Format a duration for compact status bars.

    Args:
        seconds: Duration in seconds

    Returns:
        Compact duration string
    """
    if seconds < 60:
        return f"{int(seconds)}s"
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}m{secs:02d}s"


def format_token_count(tokens: int) -> str:
    """
    Format a token count for display.

    Args:
        tokens: Token count

    Returns:
        Formatted token count string
    """
    if tokens >= 1000:
        return f"{tokens / 1000:.1f}k"
    return str(tokens)


def format_token_pair(input_tokens: int, output_tokens: int) -> Tuple[str, str]:
    """
    Format input and output token counts.

    Args:
        input_tokens: Input tokens
        output_tokens: Output tokens

    Returns:
        Tuple of (formatted_input, formatted_output)
    """
    return (format_token_count(input_tokens), format_token_count(output_tokens))


def format_key_value(key: str, value: Any, max_len: int = 0) -> str:
    """
    Format a key-value pair for display.

    Args:
        key: The key name
        value: The value to format
        max_len: Maximum length for value (0 = no limit)

    Returns:
        Formatted key=value string
    """
    val_str = str(value)
    if max_len > 0 and len(val_str) > max_len:
        val_str = val_str[: max_len - 3] + "..."

    if isinstance(value, str):
        val_str = f'"{val_str}"'

    return f"{key}={val_str}"


def format_dict_inline(data: Dict[str, Any], max_items: int = 50) -> str:
    """
    Format a dictionary as an inline string.

    Args:
        data: Dictionary to format
        max_items: Maximum items to show (default 50, essentially unlimited)

    Returns:
        Formatted inline string of key=value pairs
    """
    if not data:
        return ""

    items = []
    for i, (k, v) in enumerate(data.items()):
        if i >= max_items:
            items.append(f"+{len(data) - max_items} more")
            break
        items.append(format_key_value(k, v))

    return ", ".join(items)


def format_json_block(data: Any) -> Syntax:
    """Format data as a syntax-highlighted JSON block."""
    try:
        if isinstance(data, str):
            # Try to parse if it looks like JSON
            if data.strip().startswith("{") or data.strip().startswith("["):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    pass

        json_str = json.dumps(data, indent=2, default=str)
        return Syntax(
            json_str, "json", theme="monokai", background_color=THEME["panel_bg"]
        )
    except Exception:
        return Text(str(data))


def truncate_text(text: str, max_lines: int = 0, max_width: int = 0) -> str:
    """
    Truncate long text blocks (optional).

    Args:
        text: Text to truncate
        max_lines: Maximum lines (0 = no limit)
        max_width: Maximum line width (0 = no limit)

    Returns:
        Truncated text or original if no limits set
    """
    if max_lines == 0 and max_width == 0:
        return text

    lines = text.split("\n")
    if max_lines > 0 and len(lines) > max_lines:
        remaining = len(lines) - max_lines
        lines = lines[:max_lines]
        lines.append(f"... (+{remaining} lines)")

    if max_width > 0:
        truncated_lines = []
        for line in lines:
            if len(line) > max_width:
                truncated_lines.append(line[:max_width] + "...")
            else:
                truncated_lines.append(line)
        return "\n".join(truncated_lines)

    return "\n".join(lines)
