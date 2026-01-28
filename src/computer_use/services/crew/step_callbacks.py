"""
Step callback creation for CrewAI agents.

Handles creation of callbacks for agent step logging and dashboard updates.
"""

from typing import Callable

from ...utils.validation import is_valid_reasoning
from ...utils.ui import dashboard


class StepCallbackFactory:
    """
    Factory for creating step callbacks for CrewAI agents.
    """

    @staticmethod
    def create_step_callback(
        agent_role: str,
        agent_display_names: dict[str, str],
        is_cancelled_fn: Callable[[], bool],
        update_token_usage_fn: Callable[[], None],
    ) -> Callable:
        """
        Create a callback for agent step logging.

        Args:
            agent_role: The role/name of the agent for dashboard display
            agent_display_names: Map of agent roles to display names
            is_cancelled_fn: Function to check if cancellation was requested
            update_token_usage_fn: Function to update token usage

        Returns:
            Step callback function
        """
        display_name = agent_display_names.get(agent_role.strip(), agent_role)
        is_manager = display_name == "Manager"

        def step_callback(step_output):
            if is_cancelled_fn():
                raise KeyboardInterrupt("Task cancelled by user")

            current_agent = dashboard.get_current_agent_name()
            if is_manager and current_agent and current_agent != "Manager":
                return

            dashboard.set_agent(display_name)

            steps = step_output if isinstance(step_output, list) else [step_output]
            for step in steps:
                thought = None

                if hasattr(step, "thought") and step.thought:
                    thought = step.thought.strip()
                elif hasattr(step, "text") and step.text:
                    text = step.text.strip()
                    if "\nAction:" in text:
                        thought = text.split("\nAction:")[0].strip()
                    elif "\nFinal Answer:" in text:
                        thought = text.split("\nFinal Answer:")[0].strip()
                    elif not text.startswith(":") and len(text) > 20:
                        thought = text

                if thought:
                    thought = thought.replace("Thought:", "").strip()
                    if is_valid_reasoning(thought):
                        dashboard.set_thinking(thought)
                        dashboard._show_status("Processing...")

                if is_manager and hasattr(step, "tool"):
                    if step.tool == "Delegate work to coworker":
                        tool_input = getattr(step, "tool_input", {})
                        if isinstance(tool_input, dict):
                            agent_name = tool_input.get("coworker", "agent")
                            display_agent = agent_display_names.get(
                                agent_name.strip(), agent_name
                            )
                            task_desc = str(tool_input.get("task", "task"))[:100]
                            dashboard.log_delegation(display_agent, task_desc)

                if (
                    not is_manager
                    and hasattr(step, "tool")
                    and hasattr(step, "tool_input")
                ):
                    tool_name = step.tool
                    if tool_name and tool_name != "Delegate work to coworker":
                        dashboard._show_status(f"Running {tool_name}...")

            update_token_usage_fn()

        return step_callback
