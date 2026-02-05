"""
Agent creation service for CrewAI hierarchical crew.

Handles creation and caching of CrewAI agents with proper tool assignment.
"""

from typing import Any, Callable, Dict, List

from crewai import Agent

from ...utils.ui import dashboard


class CrewAgentFactory:
    """
    Factory for creating CrewAI agents with proper configuration.

    Handles agent creation, tool assignment, and callback setup.
    """

    @staticmethod
    def create_agent(
        config_key: str,
        config: Dict[str, Any],
        tool_names: List[str],
        llm: Any,
        tool_map: Dict[str, Any],
        platform_context: str,
        step_callback_factory: Callable,
        agent_display_names: Dict[str, str],
        multimodal: bool = False,
    ) -> Agent:
        """
        Create a CrewAI agent from configuration.

        Args:
            config_key: Key in agents config
            config: Agent configuration dictionary
            tool_names: List of tool names to assign
            llm: LLM instance for the agent
            tool_map: Map of tool names to tool instances
            platform_context: Platform context string for backstory
            step_callback_factory: Function to create step callbacks
            agent_display_names: Map of agent roles to display names
            multimodal: Whether to enable multimodal (image) support

        Returns:
            Configured CrewAI Agent instance
        """
        tools = [tool_map[name] for name in tool_names if name in tool_map]
        backstory_with_context = config["backstory"] + platform_context
        agent_role = config["role"]

        agent_params = {
            "role": agent_role,
            "goal": config["goal"],
            "backstory": backstory_with_context,
            "verbose": dashboard.is_verbose,
            "llm": llm,
            "max_iter": config.get("max_iter", 15),
            "allow_delegation": config.get("allow_delegation", False),
            "memory": False,
            "step_callback": step_callback_factory(agent_role),
        }

        if multimodal:
            agent_params["multimodal"] = True

        agent_params["tools"] = tools

        return Agent(**agent_params)

    @staticmethod
    def create_all_agents(
        agents_config: Dict[str, Any],
        tool_map: Dict[str, Any],
        platform_context: str,
        step_callback_factory: Callable,
        agent_display_names: Dict[str, str],
        llm: Any,
        vision_llm: Any,
    ) -> Dict[str, Agent]:
        """
        Create all CrewAI agents for the hierarchical crew.

        Args:
            agents_config: Full agents configuration dictionary
            tool_map: Map of tool names to tool instances
            platform_context: Platform context string
            step_callback_factory: Function to create step callbacks
            agent_display_names: Map of agent roles to display names
            llm: Default LLM for most agents
            vision_llm: Vision LLM for GUI agent

        Returns:
            Dictionary mapping agent keys to Agent instances
        """
        browser_tools = agents_config["browser_agent"].get("tools", [])
        gui_tools = agents_config["gui_agent"].get("tools", [])
        system_tools = agents_config["system_agent"].get("tools", [])
        coding_tools = agents_config["coding_agent"].get("tools", [])

        manager_agent = CrewAgentFactory.create_agent(
            config_key="manager",
            config=agents_config["manager"],
            tool_names=[],
            llm=llm,
            tool_map=tool_map,
            platform_context=platform_context,
            step_callback_factory=step_callback_factory,
            agent_display_names=agent_display_names,
        )

        return {
            "manager": manager_agent,
            "browser_agent": CrewAgentFactory.create_agent(
                config_key="browser_agent",
                config=agents_config["browser_agent"],
                tool_names=browser_tools,
                llm=llm,
                tool_map=tool_map,
                platform_context=platform_context,
                step_callback_factory=step_callback_factory,
                agent_display_names=agent_display_names,
            ),
            "gui_agent": CrewAgentFactory.create_agent(
                config_key="gui_agent",
                config=agents_config["gui_agent"],
                tool_names=gui_tools,
                llm=vision_llm,
                tool_map=tool_map,
                platform_context=platform_context,
                step_callback_factory=step_callback_factory,
                agent_display_names=agent_display_names,
            ),
            "system_agent": CrewAgentFactory.create_agent(
                config_key="system_agent",
                config=agents_config["system_agent"],
                tool_names=system_tools,
                llm=llm,
                tool_map=tool_map,
                platform_context=platform_context,
                step_callback_factory=step_callback_factory,
                agent_display_names=agent_display_names,
            ),
            "coding_agent": CrewAgentFactory.create_agent(
                config_key="coding_agent",
                config=agents_config["coding_agent"],
                tool_names=coding_tools,
                llm=llm,
                tool_map=tool_map,
                platform_context=platform_context,
                step_callback_factory=step_callback_factory,
                agent_display_names=agent_display_names,
            ),
        }
