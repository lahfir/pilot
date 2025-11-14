"""
Browser-Use tools loader.
Loads and initializes all browser tools automatically.
"""

from typing import Optional


def load_browser_tools() -> Optional[object]:
    """
    Load all Browser-Use tools dynamically.

    This function initializes and loads all available browser tools.
    Services are accessed/initialized internally - no parameters needed.

    Returns:
        Single Browser-Use Tools object with all tools registered, or None
    """
    from .twilio_tools import load_twilio_tools

    # Load Twilio tools (handles its own service initialization)
    twilio_tools = load_twilio_tools()

    if twilio_tools:
        return twilio_tools

    # Future: Merge multiple tool registries
    # Example:
    # twilio_tools = load_twilio_tools()
    # other_tools = load_other_tools()
    # if twilio_tools and other_tools:
    #     merged = Tools()
    #     merged.registry.extend(twilio_tools.registry)
    #     merged.registry.extend(other_tools.registry)
    #     return merged

    return None
