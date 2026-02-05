"""
Tests for AnalyzeImageTool integration with GUI agent.

Tests the two-step workflow:
1. get_window_image captures screenshot -> returns file path
2. analyze_image analyzes the image -> returns description
"""

import tempfile

import pytest
from PIL import Image
from unittest.mock import Mock, patch


class TestAnalyzeImageToolInitialization:
    """Test AnalyzeImageTool is properly initialized."""

    def test_analyze_image_tool_import(self):
        """AnalyzeImageTool should be importable."""
        import importlib.util
        import sys

        spec = importlib.util.spec_from_file_location(
            "analyze_image_tool",
            "src/pilot/crew_tools/analyze_image_tool.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["analyze_image_tool"] = module
        spec.loader.exec_module(module)

        assert hasattr(module, "AnalyzeImageTool")
        assert module.AnalyzeImageTool is not None

    def test_analyze_image_tool_in_crew_tools_factory(self):
        """CrewToolsFactory should include analyze_image tool."""
        from pilot.services.crew.crew_tools_factory import CrewToolsFactory

        mock_registry = Mock()
        with patch(
            "pilot.services.crew.crew_tools_factory.LLMConfig"
        ) as mock_llm_config:
            mock_llm = Mock()
            mock_llm_config.get_orchestration_llm.return_value = mock_llm

            tools = CrewToolsFactory.create_gui_tools(mock_registry)

        assert "analyze_image" in tools
        assert tools["analyze_image"] is not None

    def test_analyze_image_tool_is_custom_implementation(self):
        """analyze_image should be our custom AnalyzeImageTool, not VisionTool."""
        from pilot.services.crew.crew_tools_factory import CrewToolsFactory
        from pilot.crew_tools.analyze_image_tool import AnalyzeImageTool

        mock_registry = Mock()
        with patch(
            "pilot.services.crew.crew_tools_factory.LLMConfig"
        ) as mock_llm_config:
            mock_llm_config.get_orchestration_llm.return_value = Mock()

            tools = CrewToolsFactory.create_gui_tools(mock_registry)

        assert isinstance(tools["analyze_image"], AnalyzeImageTool)


class TestAnalyzeImageToolFunctionality:
    """Test AnalyzeImageTool handles various inputs correctly."""

    def test_analyze_image_no_path_returns_error(self):
        """AnalyzeImageTool should return error when no path provided."""
        from pilot.crew_tools.analyze_image_tool import AnalyzeImageTool

        tool = AnalyzeImageTool()
        result = tool._run(image_path="")

        assert "Error" in result
        assert "No image path" in result

    def test_analyze_image_nonexistent_file_returns_error(self):
        """AnalyzeImageTool should return error for nonexistent file."""
        from pilot.crew_tools.analyze_image_tool import AnalyzeImageTool

        tool = AnalyzeImageTool()
        result = tool._run(image_path="/nonexistent/path/image.png")

        assert "Error" in result
        assert "not found" in result


class TestGetWindowImageOutput:
    """Test get_window_image returns simplified output format."""

    @pytest.fixture
    def mock_registry(self):
        """Create mock tool registry with screenshot tool."""
        registry = Mock()

        mock_image = Mock(spec=Image.Image)
        mock_image.size = (1920, 1080)
        mock_image.save = Mock()

        mock_screenshot = Mock()
        mock_screenshot.capture = Mock(return_value=mock_image)
        mock_screenshot.capture_active_window = Mock(
            return_value=(mock_image, {"captured": True, "x": 0, "y": 0})
        )

        registry.get_tool = Mock(
            side_effect=lambda name: {"screenshot": mock_screenshot}.get(name)
        )

        return registry

    def test_get_window_image_returns_path(self, mock_registry):
        """get_window_image should return simplified output with path."""
        from pilot.crew_tools.gui_basic_tools import GetWindowImageTool

        tool = GetWindowImageTool()
        tool._tool_registry = mock_registry

        result = tool._run()

        assert result.success is True
        assert "Screenshot saved:" in result.action_taken
        assert result.data["path"] is not None
        assert result.data["path"].endswith(".png")

    def test_get_window_image_output_is_concise(self, mock_registry):
        """get_window_image output should not contain verbose instructions."""
        from pilot.crew_tools.gui_basic_tools import GetWindowImageTool

        tool = GetWindowImageTool()
        tool._tool_registry = mock_registry

        result = tool._run()

        assert "Use analyze_image tool" not in result.action_taken
        assert "to see the contents" not in result.action_taken

    def test_get_window_image_data_contains_required_fields(self, mock_registry):
        """get_window_image data should contain path, size, and app_name."""
        from pilot.crew_tools.gui_basic_tools import GetWindowImageTool

        tool = GetWindowImageTool()
        tool._tool_registry = mock_registry

        result = tool._run(app_name="Calculator")

        assert "path" in result.data
        assert "size" in result.data
        assert "app_name" in result.data
        assert result.data["app_name"] == "Calculator"

    def test_get_window_image_creates_temp_file(self, mock_registry):
        """get_window_image should create a temporary PNG file."""
        from pilot.crew_tools.gui_basic_tools import GetWindowImageTool

        tool = GetWindowImageTool()
        tool._tool_registry = mock_registry

        result = tool._run()

        path = result.data["path"]
        assert path.endswith(".png")
        assert "/tmp" in path or "var" in path or tempfile.gettempdir() in path


class TestGuiAgentMultimodalRemoved:
    """Test that GUI agent no longer uses multimodal=True."""

    def test_create_agent_without_multimodal(self):
        """GUI agent should be created without multimodal parameter."""
        from pilot.services.crew.crew_agents import CrewAgentFactory

        with patch("pilot.services.crew.crew_agents.Agent") as MockAgent:
            MockAgent.return_value = Mock()

            config = {
                "role": "GUI Agent",
                "goal": "Interact with desktop applications",
                "backstory": "Expert in GUI automation",
            }

            CrewAgentFactory.create_agent(
                config_key="gui_agent",
                config=config,
                tool_names=[],
                llm=Mock(),
                tool_map={},
                platform_context="",
                step_callback_factory=lambda x: None,
                agent_display_names={},
            )

            call_kwargs = MockAgent.call_args[1]
            assert "multimodal" not in call_kwargs

    def test_create_agent_with_multimodal_flag(self):
        """Agent should only have multimodal when explicitly passed."""
        from pilot.services.crew.crew_agents import CrewAgentFactory

        with patch("pilot.services.crew.crew_agents.Agent") as MockAgent:
            MockAgent.return_value = Mock()

            config = {
                "role": "Test Agent",
                "goal": "Test goal",
                "backstory": "Test backstory",
            }

            CrewAgentFactory.create_agent(
                config_key="test_agent",
                config=config,
                tool_names=[],
                llm=Mock(),
                tool_map={},
                platform_context="",
                step_callback_factory=lambda x: None,
                agent_display_names={},
                multimodal=True,
            )

            call_kwargs = MockAgent.call_args[1]
            assert call_kwargs.get("multimodal") is True


class TestTwoStepWorkflow:
    """Test the complete two-step image analysis workflow."""

    @pytest.fixture
    def mock_registry(self):
        """Create mock registry for workflow tests."""
        registry = Mock()

        mock_image = Mock(spec=Image.Image)
        mock_image.size = (800, 600)
        mock_image.save = Mock()

        mock_screenshot = Mock()
        mock_screenshot.capture = Mock(return_value=mock_image)
        mock_screenshot.capture_active_window = Mock(
            return_value=(mock_image, {"captured": True})
        )

        registry.get_tool = Mock(
            side_effect=lambda name: {"screenshot": mock_screenshot}.get(name)
        )

        return registry

    def test_workflow_step1_get_window_image(self, mock_registry):
        """Step 1: get_window_image captures and returns path."""
        from pilot.crew_tools.gui_basic_tools import GetWindowImageTool

        tool = GetWindowImageTool()
        tool._tool_registry = mock_registry

        result = tool._run(app_name="Finder")

        assert result.success is True
        assert result.data["path"] is not None
        path = result.data["path"]
        assert isinstance(path, str)
        assert path.endswith(".png")

    def test_workflow_analyze_image_tool_exists(self):
        """Step 2: analyze_image tool should be available in GUI tools."""
        from pilot.services.crew.crew_tools_factory import CrewToolsFactory

        mock_registry = Mock()
        with patch(
            "pilot.services.crew.crew_tools_factory.LLMConfig"
        ) as mock_llm:
            mock_llm.get_orchestration_llm.return_value = Mock()

            tools = CrewToolsFactory.create_gui_tools(mock_registry)

        assert "get_window_image" in tools
        assert "analyze_image" in tools

    def test_analyze_image_accepts_image_path(self):
        """AnalyzeImageTool should accept image_path parameter."""
        from pilot.crew_tools.analyze_image_tool import AnalyzeImageTool

        tool = AnalyzeImageTool()
        assert hasattr(tool, "_run")
        assert tool.name == "analyze_image"


class TestTempFileCleanup:
    """Test that temporary files are properly registered for cleanup."""

    @pytest.fixture
    def mock_registry(self):
        """Create mock registry."""
        registry = Mock()

        mock_image = Mock(spec=Image.Image)
        mock_image.size = (100, 100)
        mock_image.save = Mock()

        mock_screenshot = Mock()
        mock_screenshot.capture = Mock(return_value=mock_image)

        registry.get_tool = Mock(
            side_effect=lambda name: {"screenshot": mock_screenshot}.get(name)
        )

        return registry

    def test_temp_file_registered_for_cleanup(self, mock_registry):
        """Created temp files should be registered with TempFileRegistry."""
        from pilot.crew_tools.gui_basic_tools import (
            GetWindowImageTool,
            TempFileRegistry,
        )

        initial_count = len(TempFileRegistry._temp_files)

        tool = GetWindowImageTool()
        tool._tool_registry = mock_registry

        result = tool._run()
        path = result.data["path"]

        assert path in TempFileRegistry._temp_files
        assert len(TempFileRegistry._temp_files) > initial_count


class TestErrorHandling:
    """Test error handling in the vision workflow."""

    def test_get_window_image_handles_screenshot_failure(self):
        """get_window_image should handle screenshot failures gracefully."""
        from pilot.crew_tools.gui_basic_tools import GetWindowImageTool

        mock_registry = Mock()
        mock_screenshot = Mock()
        mock_screenshot.capture = Mock(side_effect=Exception("Screenshot failed"))
        mock_registry.get_tool = Mock(return_value=mock_screenshot)

        tool = GetWindowImageTool()
        tool._tool_registry = mock_registry

        result = tool._run()

        assert result.success is False
        assert result.error is not None
        assert "Screenshot failed" in result.error or "failed" in result.error.lower()

    def test_get_window_image_handles_app_window_not_found(self):
        """get_window_image should handle app window not found."""
        from pilot.crew_tools.gui_basic_tools import GetWindowImageTool

        mock_registry = Mock()
        mock_screenshot = Mock()
        mock_screenshot.capture_active_window = Mock(
            side_effect=RuntimeError("Window not found")
        )
        mock_registry.get_tool = Mock(return_value=mock_screenshot)

        tool = GetWindowImageTool()
        tool._tool_registry = mock_registry

        result = tool._run(app_name="NonExistentApp")

        assert result.success is False
        assert result.error is not None
