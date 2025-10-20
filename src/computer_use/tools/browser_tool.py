"""
Browser automation tool using Browser-Use library.
"""

from typing import Optional, Dict, Any


class BrowserTool:
    """
    Browser-Use integration for web automation.
    Browser-Use Agent handles all browser interactions internally.
    """

    def __init__(self, llm_client=None):
        """
        Initialize browser tool with Browser-Use.

        Args:
            llm_client: LLM client for Browser-Use Agent
        """
        self.browser = None
        self.llm_client = llm_client
        self.available = self._initialize_browser()

    def _initialize_browser(self) -> bool:
        """
        Initialize Browser-Use library.

        Returns:
            True if initialization successful
        """
        try:
            from browser_use import Browser

            self.Browser = Browser
            return True
        except ImportError:
            print("Browser-Use not available. Install with: pip install browser-use")
            return False

    async def execute_task(
        self, task: str, url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a web automation task using Browser-Use Agent.

        Browser-Use handles everything: navigation, clicking, typing, data extraction.
        We just pass the task and it figures out all the actions needed.

        Args:
            task: Natural language description of task (e.g., "Download HD image of Ronaldo")
            url: Optional starting URL

        Returns:
            Result dictionary with status and data
        """
        if not self.available:
            return {
                "success": False,
                "error": "Browser-Use not initialized. Install with: pip install browser-use",
            }

        if not self.llm_client:
            return {
                "success": False,
                "error": "No LLM client provided for Browser-Use Agent",
            }

        try:
            from browser_use import Agent

            full_task = f"Navigate to {url} and {task}" if url else task

            # Browser-Use Agent with its own Browser session management
            agent = Agent(task=full_task, llm=self.llm_client)

            result = await agent.run()

            return {
                "success": True,
                "message": f"Browser task completed: {task}",
                "data": {"result": str(result)},
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def close(self):
        """
        Close browser instance if needed.
        Browser-Use handles cleanup automatically.
        """
        pass
