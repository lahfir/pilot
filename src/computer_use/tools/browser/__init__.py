"""
Browser-Use tools loader.
Loads and initializes all browser tools automatically.
"""

from typing import Optional, Tuple


def load_browser_tools() -> Tuple[Optional[object], bool, bool]:
    """
    Load all Browser-Use tools dynamically.

    This function initializes and loads all available browser tools.
    Services are accessed/initialized internally - no parameters needed.

    Returns:
        Tuple of (Tools object, has_twilio, has_image_gen)
    """
    from .twilio_tools import load_twilio_tools
    from .image_tools import load_image_tools

    twilio_tools = load_twilio_tools()
    image_tools = load_image_tools()

    has_twilio = twilio_tools is not None
    has_image_gen = image_tools is not None

    if twilio_tools and image_tools:
        twilio_tools.registry.registry.actions.update(
            image_tools.registry.registry.actions
        )
        return twilio_tools, has_twilio, has_image_gen

    if twilio_tools:
        return twilio_tools, has_twilio, has_image_gen

    if image_tools:
        return image_tools, has_twilio, has_image_gen

    return None, False, False
