"""
Token usage tracking utilities for CrewAI agents.
"""

from typing import Any, Optional

from crewai import Crew

from ..ui import dashboard


def update_crew_token_usage(crew: Optional[Crew], last_update_time: float) -> float:
    """
    Update dashboard with current token usage from CrewAI crew.

    Args:
        crew: CrewAI Crew instance
        last_update_time: Timestamp of last update

    Returns:
        Updated timestamp if update occurred, original timestamp otherwise
    """
    import time

    if not crew:
        return last_update_time

    now = time.time()
    if (now - last_update_time) < 5.0:
        return last_update_time

    try:
        metrics = crew.calculate_usage_metrics()
        if metrics.prompt_tokens > 0 or metrics.completion_tokens > 0:
            dashboard.update_token_usage(
                metrics.prompt_tokens,
                metrics.completion_tokens,
            )
            return now
    except Exception:
        try:
            total_prompt = 0
            total_completion = 0
            for agent in crew.agents:
                if hasattr(agent, "llm") and hasattr(agent.llm, "_token_usage"):
                    usage = agent.llm._token_usage
                    total_prompt += usage.get("prompt_tokens", 0)
                    total_completion += usage.get("completion_tokens", 0)
            if total_prompt > 0 or total_completion > 0:
                dashboard.update_token_usage(total_prompt, total_completion)
                return now
        except Exception:
            pass
        try:
            total_prompt = 0
            total_completion = 0
            if hasattr(crew, "manager_agent") and crew.manager_agent:
                mgr = crew.manager_agent
                if hasattr(mgr, "llm") and hasattr(mgr.llm, "_token_usage"):
                    usage = mgr.llm._token_usage
                    total_prompt += usage.get("prompt_tokens", 0)
                    total_completion += usage.get("completion_tokens", 0)
            if total_prompt > 0 or total_completion > 0:
                dashboard.update_token_usage(total_prompt, total_completion)
                return now
        except Exception:
            pass

    return last_update_time


def extract_result_token_usage(result: Any) -> tuple[int, int]:
    """
    Extract token usage from CrewAI result object.

    Args:
        result: CrewAI execution result

    Returns:
        Tuple of (prompt_tokens, completion_tokens)
    """
    if not hasattr(result, "token_usage") or not result.token_usage:
        return (0, 0)

    tu = result.token_usage
    if isinstance(tu, dict):
        prompt = tu.get("prompt_tokens", 0)
        completion = tu.get("completion_tokens", 0)
    else:
        prompt = getattr(tu, "prompt_tokens", 0)
        completion = getattr(tu, "completion_tokens", 0)

    return (prompt, completion)
