"""
CrewAI-based multi-agent computer automation system.
"""

from pathlib import Path
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, Process
from .config.llm_config import LLMConfig
from .agents.gui_agent import GUIAgent
from .agents.browser_agent import BrowserAgent
from .agents.system_agent import SystemAgent
from .schemas import TaskCompletionOutput
from .crew_tools import (
    TakeScreenshotTool,
    ClickElementTool,
    TypeTextTool,
    OpenApplicationTool,
    ReadScreenTextTool,
    GetAppTextTool,
    ScrollTool,
    ListRunningAppsTool,
    CheckAppRunningTool,
    WebAutomationTool,
    ExecuteShellCommandTool,
    FindApplicationTool,
)
from .utils.coordinate_validator import CoordinateValidator
from .tools.platform_registry import PlatformToolRegistry
from .utils.ui import print_success, print_failure, print_info
import yaml
import asyncio


class TaskExecutionResult(BaseModel):
    """Result from task execution."""

    task: str = Field(..., description="Original task description")
    result: Optional[str] = Field(None, description="Execution result")
    overall_success: bool = Field(..., description="Whether execution succeeded")
    error: Optional[str] = Field(None, description="Error message if failed")


class ComputerUseCrew:
    """
    CrewAI-powered computer automation system.
    Uses CrewAI's Agent, Task, and Crew for proper multi-agent orchestration.
    """

    def __init__(
        self,
        capabilities: Any,
        safety_checker: Any,
        llm_client: Optional[Any] = None,
        vision_llm_client: Optional[Any] = None,
        browser_llm_client: Optional[Any] = None,
        confirmation_manager: Optional[Any] = None,
        twilio_service: Optional[Any] = None,
    ) -> None:
        """
        Initialize CrewAI-based automation system.

        Args:
            capabilities: PlatformCapabilities instance
            safety_checker: SafetyChecker instance
            llm_client: Optional LLM client for regular tasks
            vision_llm_client: Optional LLM client for vision tasks
            browser_llm_client: Optional LLM client for browser automation
            confirmation_manager: CommandConfirmation instance
            twilio_service: Optional TwilioService instance
        """
        self.capabilities = capabilities
        self.safety_checker = safety_checker
        self.confirmation_manager = confirmation_manager

        self.llm = llm_client or LLMConfig.get_llm()
        self.vision_llm = vision_llm_client or LLMConfig.get_vision_llm()
        self.browser_llm = browser_llm_client or LLMConfig.get_browser_llm()

        self.agents_config = self._load_yaml_config("agents.yaml")
        self.tasks_config = self._load_yaml_config("tasks.yaml")

        self.tool_registry = self._initialize_tool_registry(twilio_service)
        self._initialize_legacy_agents()

        self.gui_tools = self._initialize_gui_tools()
        self.web_automation_tool = self._initialize_web_tool()
        self.execute_command_tool = self._initialize_system_tool()

        self.crew: Optional[Crew] = None

    def _load_yaml_config(self, filename: str) -> Dict[str, Any]:
        """
        Load YAML configuration file.

        Args:
            filename: Name of YAML file in config directory

        Returns:
            Dictionary with configuration
        """
        config_path = Path(__file__).parent / "config" / filename
        with open(config_path, "r") as f:
            return yaml.safe_load(f)

    def _initialize_tool_registry(
        self, twilio_service: Optional[Any]
    ) -> PlatformToolRegistry:
        """
        Initialize platform tool registry.

        Args:
            twilio_service: Optional TwilioService instance

        Returns:
            Configured PlatformToolRegistry
        """
        coordinate_validator = CoordinateValidator(
            self.capabilities.screen_resolution[0],
            self.capabilities.screen_resolution[1],
        )

        return PlatformToolRegistry(
            self.capabilities,
            safety_checker=self.safety_checker,
            coordinate_validator=coordinate_validator,
            llm_client=self.browser_llm,
            twilio_service=twilio_service,
        )

    def _initialize_legacy_agents(self) -> None:
        """Initialize legacy agent instances for internal use."""
        self.browser_agent_instance = BrowserAgent(self.tool_registry)
        self.gui_agent_instance = GUIAgent(self.tool_registry, self.vision_llm)
        self.system_agent_instance = SystemAgent(
            self.tool_registry, self.safety_checker, self.llm
        )

    def _initialize_gui_tools(self) -> Dict[str, Any]:
        """
        Initialize and configure GUI automation tools.

        Returns:
            Dictionary mapping tool names to configured tool instances
        """
        tools = {
            "take_screenshot": TakeScreenshotTool(),
            "click_element": ClickElementTool(),
            "type_text": TypeTextTool(),
            "open_application": OpenApplicationTool(),
            "read_screen_text": ReadScreenTextTool(),
            "get_app_text": GetAppTextTool(),
            "scroll": ScrollTool(),
            "list_running_apps": ListRunningAppsTool(),
            "check_app_running": CheckAppRunningTool(),
            "find_application": FindApplicationTool(),
        }

        for tool in tools.values():
            tool._tool_registry = self.tool_registry

        tools["find_application"]._llm = self.llm

        return tools

    def _initialize_web_tool(self) -> WebAutomationTool:
        """
        Initialize and configure web automation tool.

        Returns:
            Configured WebAutomationTool instance
        """
        tool = WebAutomationTool()
        tool._tool_registry = self.tool_registry
        return tool

    def _initialize_system_tool(self) -> ExecuteShellCommandTool:
        """
        Initialize and configure system command execution tool.

        Returns:
            Configured ExecuteShellCommandTool instance
        """
        tool = ExecuteShellCommandTool()
        tool._safety_checker = self.safety_checker
        tool._confirmation_manager = self.confirmation_manager
        return tool

    def _create_manager_agent(self) -> Agent:
        """
        Create manager agent for hierarchical process.

        Returns:
            Manager Agent instance with delegation enabled
        """
        manager_config = self.agents_config.get("manager", {})

        return Agent(
            role=manager_config.get("role", "Task Orchestration Manager"),
            goal=manager_config.get("goal", "Delegate tasks efficiently"),
            backstory=manager_config.get("backstory", ""),
            verbose=manager_config.get("verbose", True),
            allow_delegation=True,
            llm=self.llm,
        )

    def _build_tool_map(self) -> Dict[str, Any]:
        """
        Build mapping of tool names to tool instances.

        Returns:
            Dictionary mapping tool names to instances
        """
        return {
            "web_automation": self.web_automation_tool,
            **self.gui_tools,
            "execute_shell_command": self.execute_command_tool,
        }

    def _create_agent(
        self,
        config_key: str,
        tool_names: List[str],
        llm: Any,
        tool_map: Dict[str, Any],
    ) -> Agent:
        """
        Create a CrewAI agent from configuration.

        Args:
            config_key: Key in agents_config for this agent
            tool_names: List of tool names to assign
            llm: LLM instance for this agent
            tool_map: Mapping of tool names to instances

        Returns:
            Configured Agent instance
        """
        config = self.agents_config[config_key]
        tools = [tool_map[name] for name in tool_names if name in tool_map]

        return Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            verbose=config.get("verbose", True),
            llm=llm,
            tools=tools,
            max_iter=config.get("max_iter", 15),
            allow_delegation=config.get("allow_delegation", False),
            output_pydantic=TaskCompletionOutput,
        )

    def _create_crewai_agents(self) -> Dict[str, Agent]:
        """
        Create CrewAI Agent instances from YAML configs.

        Returns:
            Dictionary of agent_name -> Agent instance
        """
        tool_map = self._build_tool_map()

        browser_tools = self.agents_config["browser_agent"].get("tools", [])
        gui_tools = self.agents_config["gui_agent"].get("tools", [])
        system_tools = self.agents_config["system_agent"].get("tools", [])

        return {
            "browser_agent": self._create_agent(
                "browser_agent", browser_tools, self.llm, tool_map
            ),
            "gui_agent": self._create_agent(
                "gui_agent", gui_tools, self.vision_llm, tool_map
            ),
            "system_agent": self._create_agent(
                "system_agent", system_tools, self.llm, tool_map
            ),
        }

    def _extract_context_from_history(
        self, conversation_history: List[Dict[str, Any]]
    ) -> str:
        """
        Extract context string from conversation history.

        Args:
            conversation_history: List of previous interactions

        Returns:
            Formatted context string
        """
        if not conversation_history:
            return ""

        last_interaction = conversation_history[-1]
        if "result" not in last_interaction or not last_interaction["result"]:
            return ""

        result_data = last_interaction["result"]
        if isinstance(result_data, dict) and "result" in result_data:
            return f"\n\nPREVIOUS TASK OUTPUT:\n{result_data['result']}\n"

        return ""

    async def execute_task(
        self,
        task: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> TaskExecutionResult:
        """
        Execute task using CrewAI's intelligent multi-agent orchestration.
        Uses hierarchical process with manager agent delegating to specialists,
        OR sequential process with intelligent task decomposition for complex workflows.

        Args:
            task: Natural language task description
            conversation_history: List of previous messages

        Returns:
            TaskExecutionResult with execution details
        """
        if conversation_history is None:
            conversation_history = []

        try:
            from langchain_core.messages import HumanMessage
            from pydantic import BaseModel, Field
            from typing import List as TypingList

            context_str = self._extract_context_from_history(conversation_history)
            agents_dict = self._create_crewai_agents()

            # Step 1: Analyze if task needs single agent or multiple agents
            class SubTask(BaseModel):
                agent_type: str = Field(
                    description="Agent type: 'browser', 'gui', or 'system'"
                )
                description: str = Field(
                    description="Clear, specific task description for this agent"
                )
                expected_output: str = Field(
                    description="What this agent should produce"
                )
                depends_on_previous: bool = Field(
                    description="True if this subtask needs output from previous subtask"
                )

            class TaskPlan(BaseModel):
                reasoning: str = Field(
                    description="Analysis of the task and orchestration strategy"
                )
                subtasks: TypingList[SubTask] = Field(
                    description="List of subtasks in execution order (can be 1 for simple tasks)"
                )

            orchestration_prompt = f"""You are an intelligent task orchestration system. Analyze this user request:

USER REQUEST: {task}

AGENT CAPABILITIES:
- browser: Web research, downloads, data extraction, website interaction
- gui: Desktop applications (TextEdit, Calculator, Notes, Finder, ANY GUI app), file creation via apps
- system: Shell commands, file operations via CLI

CRITICAL ANALYSIS PATTERNS:

"Research X and create/save file with results"
→ TWO subtasks: browser (get data) → gui or system (create file with that data)
→ Browser CANNOT create desktop files directly
→ Data must flow from browser → file creator

"Open app and do something"
→ ONE subtask: gui (handles entire app workflow)

"Calculate/compute something in desktop app"
→ ONE subtask: gui (opens app, performs calculation, gets result)

"Download from web"
→ ONE subtask: browser (handles download)

"Create file with specific content"
→ ONE subtask: gui (use TextEdit/Notes) OR system (use echo/cat commands)

"Find file and do something with it"
→ ONE or TWO: depends if finding requires system search or GUI navigation

ORCHESTRATION RULES:
1. If task can be completed by ONE agent → use 1 subtask
2. If task needs data from one source → used by another → use 2+ subtasks with depends_on_previous=True
3. Browser agent outputs can be used by gui/system agents (set depends_on_previous=True)
4. Each subtask must have CLEAR, ACTIONABLE description
5. Expected output must specify EXACTLY what the agent will produce

🚨 CRITICAL FOR BROWSER TASKS:
- Browser agent uses ONE web_automation tool call per subtask
- Be EXTREMELY SPECIFIC about what webpage to visit and what data to extract
- Format: "Go to [exact URL] and extract [exact data]" - NOT "research X" or "find Y"
- Example GOOD: "Navigate to https://finance.yahoo.com/quote/NVDA, extract current stock price and 5-day historical prices into structured format"
- Example BAD: "Research Nvidia stock price" (too vague, agent will hallucinate multiple steps)
- If task needs multiple web actions, create MULTIPLE browser subtasks

Analyze the request and create an optimal task plan:"""

            structured_llm = self.llm.with_structured_output(TaskPlan)
            plan = structured_llm.invoke([HumanMessage(content=orchestration_prompt)])

            print_info(f"🧠 Task Analysis: {plan.reasoning}")
            print_info(f"📋 Execution Plan: {len(plan.subtasks)} subtask(s)")
            for i, subtask in enumerate(plan.subtasks, 1):
                print_info(
                    f"  {i}. {subtask.agent_type}: {subtask.description[:70]}..."
                )

            crew_agents = []
            crew_tasks = []

            for idx, subtask in enumerate(plan.subtasks):
                agent_key = f"{subtask.agent_type}_agent"

                if agent_key not in agents_dict:
                    print_failure(f"⚠️  Invalid agent: {subtask.agent_type}, skipping")
                    continue

                agent = agents_dict[agent_key]
                crew_agents.append(agent)

                task_desc = subtask.description
                if idx == 0 and context_str:
                    task_desc = f"{task_desc}{context_str}"

                # Create CrewAI Task
                crew_task = Task(
                    description=task_desc,
                    expected_output=subtask.expected_output,
                    agent=agent,
                    output_pydantic=TaskCompletionOutput,
                    # If depends_on_previous, this task will receive previous task's output via context
                    context=(
                        [crew_tasks[-1]]
                        if subtask.depends_on_previous and crew_tasks
                        else None
                    ),
                )
                crew_tasks.append(crew_task)

            if len(crew_tasks) == 0:
                raise ValueError("No valid subtasks created from plan")

            self.crew = Crew(
                agents=list(set(crew_agents)),
                tasks=crew_tasks,
                process=Process.sequential,
                verbose=True,
            )

            print_success(
                f"🚀 Executing crew with {len(crew_agents)} agent(s) and {len(crew_tasks)} task(s)"
            )

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.crew.kickoff)

            print_success("✅ Crew execution completed!")

            return TaskExecutionResult(
                task=task,
                result=str(result),
                overall_success=True,
            )

        except Exception as e:
            print_failure(f"❌ Crew execution failed: {str(e)}")
            import traceback

            traceback.print_exc()

            return TaskExecutionResult(
                task=task,
                overall_success=False,
                error=str(e),
            )
