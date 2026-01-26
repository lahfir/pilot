"""
Observation tools for OPAV (Observe-Plan-Act-Verify) pattern.

Provides the Manager agent with system state observation capability
to enable context-aware task delegation.
"""

from pydantic import BaseModel, Field

from .instrumented_tool import InstrumentedBaseTool
from ..schemas.actions import ActionResult
from ..services.state_observer import StateObserver, ObservationScope


class GetSystemStateInput(BaseModel):
    """Input schema for system state observation."""

    scope: str = Field(
        default="standard",
        description=(
            "Observation scope: 'minimal' (fast, ~50ms), "
            "'standard' (recommended, ~200ms), or 'full' (detailed, ~300ms)"
        ),
    )


class GetSystemStateTool(InstrumentedBaseTool):
    """
    Observe current system state before delegating tasks.

    MANDATORY: Call this tool BEFORE delegating to any specialist agent.
    Include the state context in your delegation message to ensure
    specialists have accurate information about the current environment.
    """

    name: str = "get_system_state"
    description: str = (
        "MANDATORY before delegation. Observe the current system state including: "
        "active application and window, running applications, and working directory. "
        "Use this information to provide context when delegating to specialists. "
        "Scope options: 'minimal' (fastest), 'standard' (recommended), 'full' (most detail)."
    )
    args_schema: type[BaseModel] = GetSystemStateInput

    def _run(self, scope: str = "standard") -> ActionResult:
        """
        Capture current system state for context-aware delegation.

        Args:
            scope: Level of detail - 'minimal', 'standard', or 'full'.

        Returns:
            ActionResult with system state information.
        """
        if not hasattr(self, "_tool_registry") or self._tool_registry is None:
            return ActionResult(
                success=False,
                action_taken="Cannot observe system state",
                method_used="state_observation",
                confidence=0.0,
                error="Internal error: _tool_registry not set on tool instance",
            )

        try:
            scope_enum = ObservationScope(scope.lower())
        except ValueError:
            scope_enum = ObservationScope.STANDARD

        observer = StateObserver(self._tool_registry)
        state = observer.capture_state(scope_enum)

        context_string = state.to_context_string()
        running_apps_str = (
            ", ".join(state.running_apps[:10]) if state.running_apps else "None"
        )
        if len(state.running_apps) > 10:
            running_apps_str += f" (+{len(state.running_apps) - 10} more)"

        return ActionResult(
            success=True,
            action_taken=f"Observed: {state.summary}",
            method_used="state_observation",
            confidence=1.0,
            data={
                "active_app": state.active_app,
                "active_window_title": state.active_window_title,
                "running_apps": state.running_apps[:20],
                "cwd": state.cwd,
                "context_for_delegation": context_string,
            },
        )


class VerifyAppFocusedInput(BaseModel):
    """Input schema for app focus verification."""

    app_name: str = Field(
        description="Name of the application to verify (case-insensitive)"
    )


class VerifyAppFocusedTool(InstrumentedBaseTool):
    """
    Verify that a specific application is currently focused/frontmost.

    Use this before sending keyboard shortcuts or other focus-dependent actions.
    """

    name: str = "verify_app_focused"
    description: str = (
        "Check if a specific application is currently focused/frontmost. "
        "Returns True if the app is focused, False otherwise with current frontmost app. "
        "Use before sending keyboard shortcuts to ensure correct target."
    )
    args_schema: type[BaseModel] = VerifyAppFocusedInput

    def _run(self, app_name: str) -> ActionResult:
        """
        Verify if specified app is frontmost.

        Args:
            app_name: Name of application to check.

        Returns:
            ActionResult with verification status.
        """
        if not hasattr(self, "_tool_registry") or self._tool_registry is None:
            return ActionResult(
                success=False,
                action_taken=f"Cannot verify {app_name} focus",
                method_used="state_observation",
                confidence=0.0,
                error="Internal error: _tool_registry not set on tool instance",
            )

        observer = StateObserver(self._tool_registry)
        is_focused, message = observer.verify_precondition(
            "app_focused", app_name=app_name
        )

        if is_focused:
            return ActionResult(
                success=True,
                action_taken=f"Verified: {message}",
                method_used="state_observation",
                confidence=1.0,
                data={"app_name": app_name, "is_focused": True},
            )
        else:
            state = observer.capture_state(ObservationScope.MINIMAL)
            return ActionResult(
                success=True,
                action_taken=f"NOT focused: {message}",
                method_used="state_observation",
                confidence=1.0,
                error=f"{app_name} is not frontmost. Current: {state.active_app}",
                data={
                    "app_name": app_name,
                    "is_focused": False,
                    "current_frontmost": state.active_app,
                },
            )
