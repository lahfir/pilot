"""
Tests for hierarchical delegation configuration.

Verifies that the crew is configured for hierarchical process with proper delegation settings.
These tests only require YAML and don't need external dependencies.
"""

from pathlib import Path

import pytest
import yaml


@pytest.fixture
def agents_config():
    """Load the agents YAML configuration."""
    config_path = (
        Path(__file__).parent.parent / "src" / "pilot" / "config" / "agents.yaml"
    )
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestHierarchicalDelegationConfig:
    """Test suite for hierarchical delegation YAML configuration."""

    def test_manager_has_delegation_enabled(self, agents_config):
        """Verify manager has allow_delegation set to true."""
        manager_config = agents_config.get("manager", {})
        assert manager_config.get("allow_delegation") is True, (
            "Manager must have allow_delegation=true for hierarchical delegation"
        )

    def test_manager_has_role_and_goal(self, agents_config):
        """Verify manager has required role and goal."""
        manager_config = agents_config.get("manager", {})
        assert "role" in manager_config, "Manager must have a role"
        assert "goal" in manager_config, "Manager must have a goal"
        assert "backstory" in manager_config, "Manager must have a backstory"

    def test_manager_backstory_includes_delegation_instructions(self, agents_config):
        """Verify manager backstory includes delegation guidance."""
        manager_config = agents_config.get("manager", {})
        backstory = manager_config.get("backstory", "")

        assert "delegate" in backstory.lower(), (
            "Manager backstory should mention delegation"
        )
        assert "Web Automation Specialist" in backstory, (
            "Manager should know about Web Automation Specialist"
        )
        assert "Desktop Application Automation Expert" in backstory, (
            "Manager should know about Desktop Application Automation Expert"
        )

    @pytest.mark.parametrize(
        "agent_key",
        ["browser_agent", "gui_agent", "system_agent", "coding_agent"],
    )
    def test_specialist_has_delegation_disabled(self, agents_config, agent_key):
        """Verify all specialist agents have allow_delegation set to false."""
        config = agents_config.get(agent_key, {})
        assert config.get("allow_delegation") is False, (
            f"{agent_key} should have allow_delegation=false to prevent delegation loops"
        )

    @pytest.mark.parametrize(
        "agent_key",
        ["browser_agent", "gui_agent", "system_agent", "coding_agent"],
    )
    def test_specialist_has_tools(self, agents_config, agent_key):
        """Verify all specialists have tools configured."""
        config = agents_config.get(agent_key, {})
        tools = config.get("tools", [])
        assert len(tools) > 0, f"{agent_key} should have at least one tool"


class TestBrowserSessionConstraints:
    """Test that browser session constraints are preserved."""

    def test_browser_agent_single_tool_rule(self, agents_config):
        """Verify browser agent config emphasizes single web_automation call."""
        browser_config = agents_config.get("browser_agent", {})
        backstory = browser_config.get("backstory", "")

        assert "EXACTLY ONCE" in backstory, (
            "Browser agent backstory should emphasize calling web_automation EXACTLY ONCE"
        )

    def test_browser_agent_has_web_automation_tool(self, agents_config):
        """Verify browser agent has web_automation tool."""
        browser_config = agents_config.get("browser_agent", {})
        tools = browser_config.get("tools", [])

        assert "web_automation" in tools, (
            "Browser agent should have web_automation tool"
        )

    def test_browser_agent_has_limited_iterations(self, agents_config):
        """Verify browser agent has low max_iter to prevent multiple sessions."""
        browser_config = agents_config.get("browser_agent", {})
        max_iter = browser_config.get("max_iter", 15)

        assert max_iter <= 5, (
            f"Browser agent should have limited iterations (<= 5), got {max_iter}"
        )

    def test_browser_agent_session_warning(self, agents_config):
        """Verify browser agent backstory warns about session loss."""
        browser_config = agents_config.get("browser_agent", {})
        backstory = browser_config.get("backstory", "")

        assert "session" in backstory.lower() or "context" in backstory.lower(), (
            "Browser agent backstory should warn about session/context loss"
        )


class TestAgentRoles:
    """Test that agent roles are properly configured."""

    def test_all_required_agents_exist(self, agents_config):
        """Verify all required agents are configured."""
        required_agents = [
            "manager",
            "browser_agent",
            "gui_agent",
            "system_agent",
            "coding_agent",
        ]

        for agent_key in required_agents:
            assert agent_key in agents_config, f"Missing required agent: {agent_key}"

    def test_gui_agent_has_essential_tools(self, agents_config):
        """Verify GUI agent has essential interaction tools."""
        gui_config = agents_config.get("gui_agent", {})
        tools = gui_config.get("tools", [])

        essential_tools = [
            "click_element",
            "type_text",
            "read_screen_text",
            "get_accessible_elements",
        ]

        for tool in essential_tools:
            assert tool in tools, f"GUI agent missing essential tool: {tool}"

    def test_system_agent_has_shell_command(self, agents_config):
        """Verify system agent has shell command tool."""
        system_config = agents_config.get("system_agent", {})
        tools = system_config.get("tools", [])

        assert "execute_shell_command" in tools, (
            "System agent should have execute_shell_command tool"
        )

    def test_coding_agent_has_coding_automation(self, agents_config):
        """Verify coding agent has coding automation tool."""
        coding_config = agents_config.get("coding_agent", {})
        tools = coding_config.get("tools", [])

        assert "coding_automation" in tools, (
            "Coding agent should have coding_automation tool"
        )


class TestCrewPyStructure:
    """Test that crew.py has the expected structure for hierarchical delegation."""

    @pytest.fixture
    def crew_py_content(self):
        """Load the crew.py file content."""
        crew_path = Path(__file__).parent.parent / "src" / "pilot" / "crew.py"
        with open(crew_path, encoding="utf-8") as f:
            return f.read()

    def test_uses_process_hierarchical(self, crew_py_content):
        """Verify crew.py uses Process.hierarchical."""
        assert "Process.hierarchical" in crew_py_content, (
            "crew.py should use Process.hierarchical for manager delegation"
        )

    def test_has_manager_agent_parameter(self, crew_py_content):
        """Verify crew.py sets manager_agent parameter."""
        assert "manager_agent=" in crew_py_content, (
            "crew.py should set manager_agent parameter for hierarchical process"
        )

    def test_no_sequential_process(self, crew_py_content):
        """Verify crew.py doesn't use Process.sequential for main execution."""
        assert "Process.sequential" not in crew_py_content, (
            "crew.py should not use Process.sequential for main execution"
        )

    def test_no_taskplan_class(self, crew_py_content):
        """Verify crew.py doesn't have TaskPlan class."""
        assert "class TaskPlan" not in crew_py_content, (
            "crew.py should not have TaskPlan class (replaced by hierarchical delegation)"
        )

    def test_no_subtask_class(self, crew_py_content):
        """Verify crew.py doesn't have SubTask class."""
        assert "class SubTask" not in crew_py_content, (
            "crew.py should not have SubTask class (replaced by hierarchical delegation)"
        )

    def test_file_under_400_lines(self, crew_py_content):
        """Verify crew.py is under 400 lines as per project rules."""
        line_count = len(crew_py_content.splitlines())
        assert line_count <= 400, (
            f"crew.py should be under 400 lines, currently {line_count} lines"
        )
