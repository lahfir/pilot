"""
Web automation tool for CrewAI.
Wraps Browser-Use for autonomous web automation.
"""

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional
import asyncio


class WebAutomationInput(BaseModel):
    """Input for web automation.

    CRITICAL: 'task' must be a PLAIN STRING, not a dict or object!

    CORRECT:   {"task": "Search for Nvidia stock"}
    WRONG:     {"task": {"description": "...", "type": "str"}}
    """

    task: str = Field(
        ...,
        description="PLAIN STRING (not dict!) describing web task. Examples: 'Search Google for Nvidia stock price' or 'Go to yahoo.com and extract data'",
        json_schema_extra={
            "example": "Navigate to Google Finance and get NVDA stock price"
        },
    )
    url: Optional[str] = Field(
        default=None,
        description="Optional starting URL as PLAIN STRING. Example: 'https://finance.yahoo.com'",
        json_schema_extra={"example": "https://google.com"},
    )


class WebAutomationTool(BaseTool):
    """
    Autonomous web automation via Browser-Use.
    Handles navigation, data extraction, form filling, downloads.
    Phone verification handled internally via Twilio.
    """

    name: str = "web_automation"
    description: str = """Autonomous web automation using Browser-Use.
    
    Input: Provide 'task' as a PLAIN STRING (not a dict).
    Examples: 
    - task="Search for Nvidia stock price on Google Finance"
    - task="Download the latest report from example.com"
    
    Capabilities:
    - Navigate websites, click, type, fill forms
    - Extract data from pages
    - Download files (returns file path for other agents)
    - Phone verification (internal)
    
    Output: Returns extracted data and file paths that other agents can use."""
    args_schema: type[BaseModel] = WebAutomationInput

    def _run(self, task: str, url: Optional[str] = None) -> str:
        """
        Execute web automation task.
        Wraps browser_tool.execute_task.

        Args:
            task: Web task description
            url: Optional starting URL

        Returns:
            String result for CrewAI
        """
        from ..utils.ui import print_info

        print_info(f"🌐 WebAutomationTool executing: {task}")

        browser_tool = self._tool_registry.get_tool("browser")

        if not browser_tool:
            return "ERROR: Browser tool unavailable - browser tool not initialized"

        # Execute in new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(browser_tool.execute_task(task, url))

            if result.success:
                # Build structured output for CrewAI context passing
                output_parts = [f"✅ SUCCESS: {result.action_taken}"]

                # Add extracted data
                if result.data:
                    if "output" in result.data:
                        output_parts.append(
                            f"\n📊 EXTRACTED DATA:\n{result.data['output']}"
                        )
                    if "text" in result.data:
                        output_parts.append(f"\n📝 TEXT:\n{result.data['text']}")
                    if "file_path" in result.data:
                        output_parts.append(
                            f"\n📁 DOWNLOADED FILE: {result.data['file_path']}"
                        )
                    if "download_path" in result.data:
                        output_parts.append(
                            f"\n📁 DOWNLOADED FILE: {result.data['download_path']}"
                        )

                output_str = "".join(output_parts)
                print_info(f"✅ Browser automation completed: {result.action_taken}")
                return output_str
            else:
                error_str = f"❌ FAILED: {result.action_taken}\n⚠️ Error: {result.error}"
                print_info(f"❌ Browser automation failed: {result.error}")
                return error_str

        except Exception as e:
            error_msg = f"❌ ERROR: Browser automation exception - {str(e)}"
            print_info(f"❌ {error_msg}")
            return error_msg
        finally:
            loop.close()
