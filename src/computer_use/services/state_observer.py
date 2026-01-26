"""
Fast system state observation for the Observe-Plan-Act-Verify (OPAV) pattern.

Provides lightweight state capture for agents to observe system state
before taking actions, ensuring context-aware automation.
"""

import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from ..tools.platform_registry import PlatformToolRegistry


class ObservationScope(Enum):
    """Scope levels for state observation, trading detail for speed."""

    MINIMAL = "minimal"
    STANDARD = "standard"
    FULL = "full"


@dataclass
class SystemState:
    """
    Captured system state at a point in time.

    Contains information about active applications, windows, and environment
    that agents need to make informed decisions before acting.
    """

    active_app: Optional[str] = None
    active_window_title: Optional[str] = None
    running_apps: List[str] = field(default_factory=list)
    cwd: str = field(default_factory=os.getcwd)
    timestamp: float = field(default_factory=time.time)

    @property
    def summary(self) -> str:
        """One-line summary of current state."""
        app = self.active_app or "Unknown"
        window = self.active_window_title or "Unknown"
        app_count = len(self.running_apps)
        return f"Active: {app} | Window: {window} | Running: {app_count} apps"

    def to_context_string(self) -> str:
        """
        Format state for inclusion in agent delegation messages.

        Returns:
            Multi-line string describing current system state.
        """
        running = (
            ", ".join(self.running_apps[:10]) if self.running_apps else "None detected"
        )
        if len(self.running_apps) > 10:
            running += f" (+{len(self.running_apps) - 10} more)"

        return f"""CURRENT SYSTEM STATE (observed at {time.strftime("%H:%M:%S", time.localtime(self.timestamp))}):
- Active Application: {self.active_app or "Unknown"}
- Window Title: {self.active_window_title or "Unknown"}
- Running Applications: {running}
- Working Directory: {self.cwd}"""


class StateObserver:
    """
    Lightweight state capture service for OPAV pattern.

    Uses platform accessibility APIs for fast app state queries.
    Designed to add minimal overhead (<100ms for standard scope).
    """

    def __init__(self, tool_registry: "PlatformToolRegistry"):
        """
        Initialize state observer with tool registry.

        Args:
            tool_registry: Platform tool registry providing accessibility tools.
        """
        self._tool_registry = tool_registry
        self._cache: Optional[SystemState] = None
        self._cache_time: float = 0.0
        self._cache_ttl: float = 2.0

    def _get_accessibility(self) -> Optional[Any]:
        """Get the platform-appropriate accessibility tool."""
        return self._tool_registry.get_tool("accessibility")

    def capture_state(
        self, scope: ObservationScope = ObservationScope.STANDARD
    ) -> SystemState:
        """
        Capture current system state with specified detail level.

        Args:
            scope: Level of detail to capture.
                - MINIMAL: Just active app (~50ms)
                - STANDARD: Active app + running apps (~200ms)
                - FULL: All above + window title (~300ms)

        Returns:
            SystemState with captured information.
        """
        state = SystemState(cwd=os.getcwd(), timestamp=time.time())
        accessibility = self._get_accessibility()

        if not accessibility or not getattr(accessibility, "available", False):
            return state

        if scope == ObservationScope.MINIMAL:
            state.active_app = self._get_frontmost_app(accessibility)
        elif scope == ObservationScope.STANDARD:
            state.active_app = self._get_frontmost_app(accessibility)
            state.running_apps = self._get_running_apps(accessibility)
        elif scope == ObservationScope.FULL:
            state.active_app = self._get_frontmost_app(accessibility)
            state.running_apps = self._get_running_apps(accessibility)
            state.active_window_title = self._get_window_title(accessibility)

        self._cache = state
        self._cache_time = time.time()
        return state

    def _get_frontmost_app(self, accessibility: Any) -> Optional[str]:
        """Get frontmost application name."""
        try:
            if hasattr(accessibility, "get_frontmost_app"):
                return accessibility.get_frontmost_app()
            if hasattr(accessibility, "get_frontmost_app_name"):
                return accessibility.get_frontmost_app_name()
        except Exception:
            pass
        return None

    def _get_running_apps(self, accessibility: Any) -> List[str]:
        """Get list of running application names."""
        try:
            if hasattr(accessibility, "get_running_apps"):
                return accessibility.get_running_apps() or []
            if hasattr(accessibility, "get_running_app_names"):
                return accessibility.get_running_app_names() or []
        except Exception:
            pass
        return []

    def _get_window_title(self, accessibility: Any) -> Optional[str]:
        """Get title of the frontmost window."""
        try:
            if hasattr(accessibility, "get_frontmost_window_title"):
                return accessibility.get_frontmost_window_title()
            app_name = self._get_frontmost_app(accessibility)
            if app_name and hasattr(accessibility, "get_window_titles"):
                titles = accessibility.get_window_titles(app_name)
                return titles[0] if titles else None
        except Exception:
            pass
        return None

    def is_app_frontmost(self, app_name: str) -> bool:
        """
        Fast check if specific app is frontmost (<100ms).

        Args:
            app_name: Name of application to check (case-insensitive partial match).

        Returns:
            True if the app is currently frontmost.
        """
        accessibility = self._get_accessibility()
        if not accessibility or not getattr(accessibility, "available", False):
            return False

        try:
            if hasattr(accessibility, "is_app_frontmost"):
                return accessibility.is_app_frontmost(app_name)
            frontmost = self._get_frontmost_app(accessibility)
            if frontmost:
                return self._matches_name(frontmost, app_name)
        except Exception:
            pass
        return False

    def is_app_running(self, app_name: str) -> bool:
        """
        Check if an application is running.

        Args:
            app_name: Name of application to check (case-insensitive partial match).

        Returns:
            True if the app is running.
        """
        accessibility = self._get_accessibility()
        if not accessibility or not getattr(accessibility, "available", False):
            return False

        try:
            running = self._get_running_apps(accessibility)
            return any(self._matches_name(app, app_name) for app in running)
        except Exception:
            pass
        return False

    def _matches_name(self, name1: str, name2: str) -> bool:
        """Case-insensitive partial name matching."""
        if not name1 or not name2:
            return False
        n1, n2 = name1.lower(), name2.lower()
        return n1 in n2 or n2 in n1

    def verify_precondition(
        self, precondition_type: str, **kwargs: Any
    ) -> Tuple[bool, str]:
        """
        Verify a specific precondition is met.

        Args:
            precondition_type: Type of precondition to check.
                - "app_focused": Check if specific app is frontmost
                - "app_running": Check if specific app is running
                - "file_exists": Check if file path exists
                - "dir_exists": Check if directory exists
            **kwargs: Arguments for the precondition check.

        Returns:
            Tuple of (is_valid, message) describing the result.
        """
        if precondition_type == "app_focused":
            app_name = kwargs.get("app_name", "")
            if self.is_app_frontmost(app_name):
                return True, f"{app_name} is frontmost"
            frontmost = self._get_frontmost_app(self._get_accessibility())
            return (
                False,
                f"{app_name} is NOT frontmost (current: {frontmost or 'Unknown'})",
            )

        if precondition_type == "app_running":
            app_name = kwargs.get("app_name", "")
            if self.is_app_running(app_name):
                return True, f"{app_name} is running"
            return False, f"{app_name} is NOT running"

        if precondition_type == "file_exists":
            path = kwargs.get("path", "")
            if os.path.isfile(path):
                return True, f"File exists: {path}"
            return False, f"File does NOT exist: {path}"

        if precondition_type == "dir_exists":
            path = kwargs.get("path", "")
            if os.path.isdir(path):
                return True, f"Directory exists: {path}"
            return False, f"Directory does NOT exist: {path}"

        return True, f"Unknown precondition type: {precondition_type}"

    def get_cached_state(self) -> Optional[SystemState]:
        """
        Get cached state if still valid.

        Returns:
            Cached SystemState if within TTL, None otherwise.
        """
        if self._cache and (time.time() - self._cache_time) < self._cache_ttl:
            return self._cache
        return None
