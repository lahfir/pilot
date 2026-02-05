"""
Services module - organized by domain.

Submodules:
- crew: Agent creation, execution, and event handling
- voice: Audio capture and voice input
- state: Application and system state management
- external: External service integrations (Twilio, webhooks)
"""

from .crew import (
    CrewAgentFactory,
    CrewExecutor,
    CrewGuiDelegate,
    CrewToolsFactory,
    LLMEventService,
    StepCallbackFactory,
)
from .external import TwilioService, WebhookServer
from .state import AppStateManager, get_app_state

__all__ = [
    "CrewAgentFactory",
    "CrewExecutor",
    "CrewGuiDelegate",
    "CrewToolsFactory",
    "LLMEventService",
    "StepCallbackFactory",
    "TwilioService",
    "WebhookServer",
    "AppStateManager",
    "get_app_state",
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
        from .voice import AudioCapture

        return AudioCapture
    elif name == "VoiceInputService":
        from .voice import VoiceInputService

        return VoiceInputService
    elif name == "StateObserver":
        from .state import StateObserver

        return StateObserver
    elif name == "SystemState":
        from .state import SystemState

        return SystemState
    elif name == "ObservationScope":
        from .state import ObservationScope

        return ObservationScope
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
