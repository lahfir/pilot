"""
Platform-aware tool registry for dynamic tool serving.
"""

from typing import Dict, Any, List
from .screenshot_tool import ScreenshotTool
from .input_tool import InputTool
from .process_tool import ProcessTool
from .file_tool import FileTool
from .browser_tool import BrowserTool
from .accessibility.macos_accessibility import MacOSAccessibility
from .accessibility.windows_accessibility import WindowsAccessibility
from .accessibility.linux_accessibility import LinuxAccessibility
from .vision.ocr_tool import OCRTool
from .vision.template_matcher import TemplateMatcher
from .vision.element_detector import ElementDetector
from .fallback.vision_coordinates import VisionCoordinateTool


class PlatformToolRegistry:
    """
    Dynamically loads and serves tools based on detected platform capabilities.
    """

    def __init__(
        self,
        capabilities,
        safety_checker=None,
        coordinate_validator=None,
        browser_llm_client=None,
    ):
        """
        Initialize tool registry with platform capabilities.

        Args:
            capabilities: PlatformCapabilities object
            safety_checker: Optional SafetyChecker instance
            coordinate_validator: Optional CoordinateValidator instance
            browser_llm_client: Browser-Use compatible LLM client
        """
        self.capabilities = capabilities
        self.safety_checker = safety_checker
        self.coordinate_validator = coordinate_validator
        self.browser_llm_client = browser_llm_client
        self.tools = self._initialize_tools()

    def _initialize_tools(self) -> Dict[str, Any]:
        """
        Load appropriate tools for current platform.

        Returns:
            Dictionary of initialized tools
        """
        tools = {}

        if self.capabilities.accessibility_api_available:
            if self.capabilities.os_type == "macos":
                tools["accessibility"] = MacOSAccessibility()
            elif self.capabilities.os_type == "windows":
                tools["accessibility"] = WindowsAccessibility()
            elif self.capabilities.os_type == "linux":
                tools["accessibility"] = LinuxAccessibility()

        tools["ocr"] = OCRTool()
        tools["template_matcher"] = TemplateMatcher()
        tools["element_detector"] = ElementDetector()

        tools["vision_coordinates"] = VisionCoordinateTool()

        tools["screenshot"] = ScreenshotTool()
        tools["input"] = InputTool(validator=self.coordinate_validator)
        tools["process"] = ProcessTool()
        tools["file"] = FileTool(safety_checker=self.safety_checker)
        tools["browser"] = BrowserTool(llm_client=self.browser_llm_client)

        return tools

    def get_gui_tools(self) -> List[Any]:
        """
        Get GUI automation tools in priority order.

        Returns:
            List of tools ordered by accuracy (highest first)
        """
        ordered_tools = []

        if "accessibility" in self.tools:
            ordered_tools.append(self.tools["accessibility"])

        ordered_tools.extend(
            [
                self.tools["ocr"],
                self.tools["element_detector"],
                self.tools["vision_coordinates"],
            ]
        )

        return ordered_tools

    def get_tool(self, tool_name: str) -> Any:
        """
        Get a specific tool by name.

        Args:
            tool_name: Name of tool to retrieve

        Returns:
            Tool instance or None if not available
        """
        return self.tools.get(tool_name)

    def list_available_tools(self) -> List[str]:
        """
        List names of all available tools.

        Returns:
            List of tool names
        """
        return list(self.tools.keys())

    def get_capabilities_summary(self) -> Dict[str, Any]:
        """
        Get summary of platform capabilities and available tools.

        Returns:
            Dictionary with capability information
        """
        return {
            "os_type": self.capabilities.os_type,
            "os_version": self.capabilities.os_version,
            "accessibility_api": self.capabilities.accessibility_api_type,
            "screen_resolution": self.capabilities.screen_resolution,
            "available_tools": self.list_available_tools(),
            "tier1_available": "accessibility" in self.tools,
            "tier2_available": True,
            "tier3_available": True,
        }
