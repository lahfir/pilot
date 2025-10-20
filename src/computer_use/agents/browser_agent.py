"""
Browser agent for web automation using Browser-Use.
"""

from typing import Dict, Any


class BrowserAgent:
    """
    Web automation specialist using Browser-Use library.
    Handles all web-based tasks with high accuracy.
    """

    def __init__(self, tool_registry):
        """
        Initialize browser agent.

        Args:
            tool_registry: PlatformToolRegistry instance
        """
        self.tool_registry = tool_registry
        self.browser_tool = tool_registry.get_tool("browser")

    async def execute_task(
        self, task: str, url: str = None, context: dict = None
    ) -> Dict[str, Any]:
        """
        Execute web automation task.

        Args:
            task: Natural language task description
            url: Optional starting URL
            context: Context from previous agents

        Returns:
            Result dictionary with status and data
        """
        enhanced_task = task
        if context and context.get("previous_results"):
            prev_results = context.get("previous_results", [])
            if prev_results:
                context_info = "CONTEXT - Previous work done:\n"
                for res in prev_results:
                    agent_type = res.get("method_used", "unknown")
                    action = res.get("action_taken", "")
                    success = "✅" if res.get("success") else "❌"
                    context_info += f"{success} {agent_type}: {action}\n"
                enhanced_task = f"{context_info}\n\nYOUR TASK: {task}"

        try:
            result = await self.browser_tool.execute_task(enhanced_task, url)

            return {
                "success": result.get("success", False),
                "action_taken": task,
                "method_used": "browser",
                "confidence": 1.0 if result.get("success") else 0.0,
                "data": result.get("data", {}),
                "error": result.get("error"),
            }
        except Exception as e:
            return {
                "success": False,
                "action_taken": task,
                "method_used": "browser",
                "confidence": 0.0,
                "error": str(e),
            }
