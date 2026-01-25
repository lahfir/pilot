"""
Centralized application state management.

Single source of truth for tracking the currently active/target application
across all tools and agents.
"""

import threading
from dataclasses import dataclass
from typing import Optional


@dataclass
class AppStateSnapshot:
    """Immutable snapshot of app state at a point in time."""

    target_app: Optional[str]
    actual_frontmost: Optional[str]
    is_synced: bool


class AppStateManager:
    """
    Thread-safe singleton for managing current application state.

    Provides a single source of truth for:
    - The target app (what we're trying to interact with)
    - Synchronization with actual frontmost app
    """

    _instance: Optional["AppStateManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "AppStateManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._target_app: Optional[str] = None
        self._accessibility_tool = None
        self._initialized = True

    def set_accessibility_tool(self, accessibility_tool) -> None:
        """Set the accessibility tool for frontmost app queries."""
        self._accessibility_tool = accessibility_tool

    def set_target_app(self, app_name: str) -> None:
        """Set the current target application."""
        self._target_app = app_name

    def get_target_app(self) -> Optional[str]:
        """Get the current target application."""
        return self._target_app

    def clear_target_app(self) -> None:
        """Clear the target app (e.g., when task completes)."""
        self._target_app = None

    def get_frontmost_app(self) -> Optional[str]:
        """Get the actual frontmost application from the system."""
        if self._accessibility_tool and hasattr(
            self._accessibility_tool, "get_frontmost_app"
        ):
            return self._accessibility_tool.get_frontmost_app()
        return None

    def get_effective_app(self, explicit_app: Optional[str] = None) -> Optional[str]:
        """
        Get the effective app to use for operations.

        Priority:
        1. Explicitly passed app_name (highest priority)
        2. Current target app (if set)
        3. Actual frontmost app (fallback)
        """
        if explicit_app:
            return explicit_app
        if self._target_app:
            return self._target_app
        return self.get_frontmost_app()

    def get_state(self) -> AppStateSnapshot:
        """Get current state snapshot."""
        frontmost = self.get_frontmost_app()
        is_synced = (
            self._target_app is not None
            and frontmost is not None
            and self._target_app.lower() == frontmost.lower()
        )
        return AppStateSnapshot(
            target_app=self._target_app,
            actual_frontmost=frontmost,
            is_synced=is_synced,
        )

    def is_target_frontmost(self) -> bool:
        """Check if target app is currently frontmost."""
        if not self._target_app:
            return False
        frontmost = self.get_frontmost_app()
        if not frontmost:
            return False
        return self._target_app.lower() == frontmost.lower()


def get_app_state() -> AppStateManager:
    """Get the global app state manager instance."""
    return AppStateManager()
