"""
Coding automation tool for CrewAI.
Wraps CodingAgent (Cline CLI) for autonomous code automation.
"""

from pydantic import BaseModel, Field
import asyncio
import concurrent.futures

from .instrumented_tool import InstrumentedBaseTool


class CodingAutomationInput(BaseModel):
    """Input schema for coding automation tool."""

    task: str = Field(
        ...,
        description="The coding task to execute (plain text string)",
    )


class CodingAgentTool(InstrumentedBaseTool):
    """
    Autonomous coding automation via Cline CLI.
    Handles code writing, refactoring, bug fixes, tests, and features.
    """

    name: str = "coding_automation"
    description: str = (
        "Execute coding tasks using Cline AI. "
        "Pass a single 'task' string describing what code to write, fix, or modify. "
        "Example: coding_automation(task='Create a Python snake game with pygame')"
    )
    args_schema: type[BaseModel] = CodingAutomationInput

    def _run(self, task: str) -> str:
        """
        Execute coding task via CodingAgent.

        Args:
            task: Coding task description

        Returns:
            String result for CrewAI
        """
        from ..utils.ui import dashboard, ActionType
        from ..utils.ui.core.responsive import ResponsiveWidth

        if dashboard.get_current_agent_name() == "Manager":
            dashboard.set_agent("Coding Agent")
            excerpt = ResponsiveWidth.truncate(task, max_ratio=0.7, min_width=40)
            dashboard.set_thinking(f"Coding task: {excerpt}")

        dashboard.add_log_entry(ActionType.EXECUTE, f"CodingAgentTool: {task}")

        coding_agent = self._coding_agent

        if not coding_agent:
            return "ERROR: Coding agent unavailable - not initialized"

        try:
            running_loop = asyncio.get_running_loop()
        except RuntimeError:
            running_loop = None

        if running_loop and running_loop.is_running():
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, coding_agent.execute_task(task))
                result = future.result()
        else:
            result = asyncio.run(coding_agent.execute_task(task))

        try:
            if result.success:
                output_parts = [f"✅ SUCCESS: {result.action_taken}"]

                if result.data:
                    if "output" in result.data:
                        output_parts.append(f"\n📝 OUTPUT:\n{result.data['output']}")

                output_str = "".join(output_parts)
                dashboard.add_log_entry(
                    ActionType.COMPLETE,
                    f"Coding completed: {result.action_taken}",
                    status="complete",
                )
                return output_str
            else:
                error_str = f"❌ FAILED: {result.action_taken}\n⚠️ Error: {result.error}"
                dashboard.add_log_entry(
                    ActionType.ERROR, f"Coding failed: {result.error}", status="error"
                )
                raise Exception(error_str)
        except Exception as e:
            error_msg = f"Coding automation exception: {str(e)}"
            dashboard.add_log_entry(ActionType.ERROR, error_msg, status="error")
            raise Exception(f"❌ ERROR: {error_msg}")
