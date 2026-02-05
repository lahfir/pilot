"""
Reasoning validation utilities for filtering agent output.

Helps distinguish valid reasoning from tool output, prompts, and other noise.
"""


def is_valid_reasoning(text: str) -> bool:
    """
    Check if text is valid reasoning vs tool output/junk/verbose prompts.

    Args:
        text: Text to validate

    Returns:
        True if valid reasoning worth displaying
    """
    if not text or len(text) < 10:
        return False

    text_lower = text.lower()

    if "delegate" in text_lower or "delegating" in text_lower:
        return True

    invalid_starts = [
        ": true",
        ": false",
        ": none",
        "true",
        "false",
        "none",
        "success=",
        "error=",
        '{"',
        "{'",
        "action:",
    ]
    for pattern in invalid_starts:
        if text_lower.startswith(pattern):
            return False

    invalid_contains = [
        "use the following format",
        "begin!",
    ]
    for pattern in invalid_contains:
        if pattern.lower() in text_lower:
            return False

    if len(text) > 300:
        return False

    return True
