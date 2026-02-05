"""
External service integrations for Twilio and webhooks.
"""

from .twilio_service import TwilioService

try:
    from .webhook_server import WebhookServer

    _webhook_available = True
except ImportError:
    WebhookServer = None
    _webhook_available = False

__all__ = [
    "TwilioService",
    "WebhookServer",
]


def __getattr__(name):
    """
    Lazy import for webhook server if Flask not available.
    """
    if name == "WebhookServer" and not _webhook_available:
        raise ImportError(
            "WebhookServer requires Flask. Install with: pip install flask"
        )
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
