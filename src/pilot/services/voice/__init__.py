"""
Voice and audio services for speech input and processing.
"""

__all__ = [
    "AudioCapture",
    "VoiceInputService",
]


def __getattr__(name):
    """
    Lazy import for optional voice services to avoid dependency issues.
    """
    if name == "AudioCapture":
        from .audio_capture import AudioCapture

        return AudioCapture
    elif name == "VoiceInputService":
        from .voice_input_service import VoiceInputService

        return VoiceInputService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
