"""
LLM event handlers for CrewAI integration.

Subscribes to CrewAI LLM events and updates dashboard with real-time status.
"""

from typing import Any

from crewai.events.event_bus import crewai_event_bus
from crewai.events.types.llm_events import (
    LLMCallCompletedEvent,
    LLMCallFailedEvent,
    LLMCallStartedEvent,
)

from ...utils.logging import (
    debug_log,
    get_debug_llm_event_limit,
    increment_debug_llm_events_logged,
)
from ...utils.ui import dashboard


class LLMEventService:
    """
    Service for handling CrewAI LLM events and updating dashboard.

    Subscribes to LLM call events and provides real-time status updates
    to the dashboard UI.
    """

    _handlers_registered: bool = False

    @classmethod
    def setup_handlers(cls) -> None:
        """
        Subscribe to CrewAI LLM events for real-time status updates.

        This method is idempotent - calling it multiple times will only
        register handlers once.
        """
        if cls._handlers_registered:
            return

        cls._handlers_registered = True

        try:

            @crewai_event_bus.on(LLMCallStartedEvent)
            def on_llm_start(source: Any, event: LLMCallStartedEvent) -> None:
                model = getattr(event, "model", "LLM") or "LLM"
                model_name = (
                    str(model).split("/")[-1] if "/" in str(model) else str(model)
                )
                if increment_debug_llm_events_logged() <= get_debug_llm_event_limit():
                    debug_log(
                        "H_CREW_LLM_EVENTS",
                        "llm_events.py:on_llm_start",
                        "LLM call started",
                        {
                            "agent": dashboard.get_current_agent_name() or "Agent",
                            "model_name": model_name,
                            "event_model_type": type(model).__name__,
                        },
                    )
                dashboard.log_llm_start(model_name)
                agent = dashboard.get_current_agent_name() or "Agent"
                if agent == "Manager":
                    dashboard._show_status(f"Thinking • {model_name}")
                else:
                    dashboard._show_status(f"Reasoning • {model_name}")

            @crewai_event_bus.on(LLMCallCompletedEvent)
            def on_llm_complete(source: Any, event: LLMCallCompletedEvent) -> None:
                prompt_tokens = 0
                completion_tokens = 0
                usage = getattr(event, "usage", None) or getattr(
                    event, "token_usage", None
                )
                if usage:
                    if isinstance(usage, dict):
                        prompt_tokens = usage.get("prompt_tokens")
                        if prompt_tokens is None:
                            prompt_tokens = usage.get("input_tokens", 0)
                        completion_tokens = usage.get("completion_tokens")
                        if completion_tokens is None:
                            completion_tokens = usage.get("output_tokens", 0)
                    else:
                        prompt_tokens = getattr(usage, "prompt_tokens", None)
                        if prompt_tokens is None:
                            prompt_tokens = getattr(usage, "input_tokens", 0)
                        completion_tokens = getattr(usage, "completion_tokens", None)
                        if completion_tokens is None:
                            completion_tokens = getattr(usage, "output_tokens", 0)

                if increment_debug_llm_events_logged() <= get_debug_llm_event_limit():
                    debug_log(
                        "H_CREW_LLM_EVENTS",
                        "llm_events.py:on_llm_complete",
                        "LLM call completed",
                        {
                            "agent": dashboard.get_current_agent_name() or "Agent",
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens,
                            "has_response": bool(getattr(event, "response", None)),
                        },
                    )

                dashboard.log_llm_complete(prompt_tokens, completion_tokens)
                agent = dashboard.get_current_agent_name() or "Agent"

                response = getattr(event, "response", None)
                if response:
                    reasoning = None
                    if isinstance(response, dict):
                        reasoning = response.get("reasoning_content") or response.get(
                            "thinking"
                        )
                    elif hasattr(response, "reasoning_content"):
                        reasoning = response.reasoning_content
                    elif hasattr(response, "thinking"):
                        reasoning = response.thinking

                    if reasoning and len(str(reasoning)) > 20:
                        dashboard.set_thinking(f"💭 {str(reasoning)[:200]}...")

                if agent == "Manager":
                    dashboard._show_status("Deciding next action...")
                else:
                    dashboard._show_status("Executing...")

            @crewai_event_bus.on(LLMCallFailedEvent)
            def on_llm_failed(source: Any, event: LLMCallFailedEvent) -> None:
                error_msg = getattr(event, "error", None) or getattr(
                    event, "message", None
                )
                error_type = type(error_msg).__name__ if error_msg else "Unknown"
                model = getattr(event, "model", "LLM") or "LLM"
                print(f"\n[LLM ERROR] {error_type}: {str(error_msg)[:200]}")
                debug_log(
                    "H_CREW_LLM_EVENTS",
                    "llm_events.py:on_llm_failed",
                    "LLM call FAILED",
                    {
                        "agent": dashboard.get_current_agent_name() or "Agent",
                        "model": str(model),
                        "error_type": error_type,
                        "error_msg": str(error_msg)[:500] if error_msg else "None",
                    },
                )
                dashboard._show_status(f"LLM Error: {str(error_msg)[:80]}...")

        except Exception:
            pass
