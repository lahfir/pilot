"""
State management services for application and system state.
"""

from .app_state import AppStateManager, get_app_state

__all__ = [
    "AppStateManager",
    "get_app_state",
    "StateObserver",
    "SystemState",
    "ObservationScope",
]


def __getattr__(name):
    """
    Lazy import for state observer to avoid circular imports.
    """
    if name == "StateObserver":
        from .state_observer import StateObserver

        return StateObserver
    elif name == "SystemState":
        from .state_observer import SystemState

        return SystemState
    elif name == "ObservationScope":
        from .state_observer import ObservationScope

        return ObservationScope
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
