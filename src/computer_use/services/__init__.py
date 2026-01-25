"""
Services module for external integrations.
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
    "AudioCapture",
    "VoiceInputService",
    "StateObserver",
    "SystemState",
    "ObservationScope",
]


def __getattr__(name):
    """
    Lazy import for optional services to avoid dependency issues.
    """
    if name == "AudioCapture":
        from .audio_capture import AudioCapture

        return AudioCapture
    elif name == "VoiceInputService":
        from .voice_input_service import VoiceInputService

        return VoiceInputService
    elif name == "WebhookServer" and not _webhook_available:
        raise ImportError(
            "WebhookServer requires Flask. Install with: pip install flask"
        )
    elif name == "StateObserver":
        from .state_observer import StateObserver

        return StateObserver
    elif name == "SystemState":
        from .state_observer import SystemState

        return SystemState
    elif name == "ObservationScope":
        from .state_observer import ObservationScope

        return ObservationScope
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
