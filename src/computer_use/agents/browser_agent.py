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

    async def execute_task(self, task: str, url: str = None) -> Dict[str, Any]:
        """
        Execute web automation task.

        Args:
            task: Natural language task description
            url: Optional starting URL

        Returns:
            Result dictionary with status and data
        """
        try:
            result = await self.browser_tool.execute_task(task, url)

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

