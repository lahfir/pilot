"""
CrewAI-compatible tool wrappers for our custom agents.
Bridges our specialized agents with CrewAI's tool execution system.
"""

from typing import TYPE_CHECKING, Any
import asyncio
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from ..schemas.browser_output import BrowserOutput

if TYPE_CHECKING:
    from ..agents.browser_agent import BrowserAgent  # noqa: F401
    from ..agents.gui_agent import GUIAgent  # noqa: F401
    from ..agents.system_agent import SystemAgent  # noqa: F401


class BrowserToolInput(BaseModel):
    """Input schema for browser automation tool."""

    task: str = Field(description="Natural language description of the web task to perform")


class GUIToolInput(BaseModel):
    """Input schema for GUI automation tool."""

    task: str = Field(description="Natural language description of the GUI task to perform")


class SystemToolInput(BaseModel):
    """Input schema for system operations tool."""

    task: str = Field(description="Natural language description of the system operation to perform")


class BrowserAutomationTool(BaseTool):
    """
    CrewAI tool wrapper for browser automation.
    """

    name: str = "browser_automation"
    description: str = """
    Automate web browsing, research, and data extraction.
    
    Use this tool to:
    - Search for information online
    - Navigate websites and extract data
    - Download files from the internet
    - Research and gather information
    
    Input: Natural language task description (e.g., "Research convertible sofa designs from Pinterest")
    Output: Task results with file paths and extracted data
    """
    args_schema: type[BaseModel] = BrowserToolInput

    browser_agent: Any = Field(description="Browser agent instance", exclude=True)

    def _run(self, task: str) -> str:
        """
        Execute browser automation task.

        Args:
            task: Natural language task description

        Returns:
            String result from browser agent
        """
        result = asyncio.run(self.browser_agent.execute_task(task))

        if result.success:
            output_text = "✅ Browser task completed successfully\n\n"

            if result.data and "output" in result.data:
                try:
                    browser_output = BrowserOutput(**result.data["output"])
                    output_text += f"Summary: {browser_output.text}\n\n"

                    if browser_output.has_files():
                        output_text += (
                            f"Files created ({browser_output.get_file_count()}):\n"
                        )
                        for file_detail in browser_output.file_details:
                            output_text += f"  • {file_detail.name} ({file_detail.size / 1024:.1f} KB)\n"
                            output_text += f"    Path: {file_detail.path}\n"
                except Exception:
                    output_text += str(result.data.get("output", ""))

            return output_text
        else:
            return f"❌ Browser task failed: {result.error}"


class GUIAutomationTool(BaseTool):
    """
    CrewAI tool wrapper for GUI automation.
    """

    name: str = "gui_automation"
    description: str = """
    Interact with desktop applications using GUI automation.
    
    Use this tool to:
    - Open desktop applications
    - Click buttons and interact with UI elements
    - Type text into applications
    - Work with visual interfaces
    
    Input: Task description with specific app and actions
    Output: Result of GUI interaction
    """
    args_schema: type[BaseModel] = GUIToolInput

    gui_agent: Any = Field(description="GUI agent instance", exclude=True)

    def _run(self, task: str) -> str:
        """
        Execute GUI automation task.

        Args:
            task: Natural language task description

        Returns:
            String result from GUI agent
        """
        result = asyncio.run(self.gui_agent.execute_task(task))

        if result.success:
            return f"✅ GUI task completed: {result.action_taken}"
        else:
            return f"❌ GUI task failed: {result.error}"


class SystemOperationsTool(BaseTool):
    """
    CrewAI tool wrapper for system operations.
    """

    name: str = "system_operations"
    description: str = """
    Execute system commands, manage files, and perform file operations.
    
    Use this tool to:
    - Copy, move, or organize files
    - Verify file existence
    - Execute shell commands
    - Manage directories
    
    Input: Task description with file operations or commands needed
    Output: Result of system operations
    """
    args_schema: type[BaseModel] = SystemToolInput

    system_agent: Any = Field(description="System agent instance", exclude=True)
    confirmation_manager: Any = Field(description="Command confirmation manager", exclude=True)

    def _run(self, task: str) -> str:
        """
        Execute system operations task.

        Args:
            task: Natural language task description

        Returns:
            String result from system agent
        """
        context = {"confirmation_manager": self.confirmation_manager}
        result = asyncio.run(self.system_agent.execute_task(task, context))

        if result.success:
            return f"✅ System task completed: {result.action_taken}"
        else:
            return f"❌ System task failed: {result.error}"
