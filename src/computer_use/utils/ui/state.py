"""
State management for the UI: Dataclasses and activity tracking.
"""

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Literal, Optional


class VerbosityLevel(Enum):
    """Verbosity levels for UI output."""

    QUIET = 0
    NORMAL = 1
    VERBOSE = 2


class ActionType(Enum):
    """Types of actions for visual distinction."""

    CLICK = "click"
    TYPE = "type"
    SCROLL = "scroll"
    OPEN = "open"
    READ = "read"
    SEARCH = "search"
    NAVIGATE = "navigate"
    ANALYZE = "analyze"
    EXECUTE = "execute"
    PLAN = "plan"
    COMPLETE = "complete"
    ERROR = "error"
    WEBHOOK = "webhook"


@dataclass
class ToolState:
    """State of a single tool execution."""

    tool_id: str
    name: str
    status: Literal["pending", "running", "success", "error"] = "pending"
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Optional[Any] = None
    error: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration: float = 0.0

    def complete(self, success: bool, output: Any = None, error: str = None):
        self.status = "success" if success else "error"
        self.output_data = output
        self.error = error
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time


@dataclass
class LLMCallState:
    """State of a single LLM call for timing tracking."""

    call_id: str
    model: str
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration: float = 0.0
    status: Literal["pending", "complete", "error"] = "pending"
    prompt_tokens: int = 0
    completion_tokens: int = 0

    def complete(self, prompt_tokens: int = 0, completion_tokens: int = 0):
        """Mark LLM call as complete and calculate duration."""
        self.status = "complete"
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens

    @property
    def elapsed(self) -> float:
        """Get elapsed time (for in-progress calls)."""
        if self.end_time:
            return self.duration
        return time.time() - self.start_time


@dataclass
class AgentState:
    """State of an agent."""

    agent_id: str
    name: str
    status: Literal["idle", "thinking", "executing", "complete", "error"] = "idle"
    current_thought: Optional[str] = None
    tools: List[ToolState] = field(default_factory=list)
    active_tool_id: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    llm_calls: List[LLMCallState] = field(default_factory=list)
    active_llm_call_id: Optional[str] = None

    @property
    def duration(self) -> float:
        """Calculate agent's active duration."""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time

    @property
    def total_llm_time(self) -> float:
        """Total time spent in LLM calls."""
        return sum(call.duration for call in self.llm_calls if call.status == "complete")

    @property
    def total_tool_time(self) -> float:
        """Total time spent in tool executions."""
        return sum(tool.duration for tool in self.tools if tool.status in ("success", "error"))

    @property
    def llm_call_count(self) -> int:
        """Number of completed LLM calls."""
        return sum(1 for call in self.llm_calls if call.status == "complete")

    def add_tool(self, name: str, input_data: Any) -> ToolState:
        tool_id = str(uuid.uuid4())
        tool = ToolState(
            tool_id=tool_id,
            name=name,
            input_data=(
                input_data if isinstance(input_data, dict) else {"value": input_data}
            ),
        )
        self.tools.append(tool)
        self.active_tool_id = tool_id
        self.status = "executing"
        return tool

    def get_tool(self, tool_id: str) -> Optional[ToolState]:
        for tool in self.tools:
            if tool.tool_id == tool_id:
                return tool
        return None

    def get_active_tool(self) -> Optional[ToolState]:
        if not self.active_tool_id:
            return None
        return self.get_tool(self.active_tool_id)

    def start_llm_call(self, model: str) -> LLMCallState:
        """Start tracking a new LLM call."""
        call_id = str(uuid.uuid4())
        llm_call = LLMCallState(call_id=call_id, model=model)
        self.llm_calls.append(llm_call)
        self.active_llm_call_id = call_id
        self.status = "thinking"
        return llm_call

    def complete_llm_call(self, prompt_tokens: int = 0, completion_tokens: int = 0):
        """Complete the active LLM call."""
        if self.active_llm_call_id:
            for call in self.llm_calls:
                if call.call_id == self.active_llm_call_id:
                    call.complete(prompt_tokens, completion_tokens)
                    break
            self.active_llm_call_id = None

    def get_active_llm_call(self) -> Optional[LLMCallState]:
        """Get the currently active LLM call."""
        if not self.active_llm_call_id:
            return None
        for call in self.llm_calls:
            if call.call_id == self.active_llm_call_id:
                return call
        return None


@dataclass
class TaskState:
    """Global state of the current task."""

    task_id: str
    description: str
    status: Literal["pending", "running", "complete", "error"] = "pending"
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    agents: Dict[str, AgentState] = field(default_factory=dict)
    active_agent_id: Optional[str] = None
    token_input: int = 0
    token_output: int = 0
    total_tools: int = 0
    failed_tools: int = 0
    browser_agent_executed: bool = False
    external_tools_executed: bool = False
    current_phase: Literal["idle", "thinking", "executing", "waiting"] = "idle"
    phase_start_time: float = field(default_factory=time.time)
    current_operation: Optional[str] = None

    @property
    def phase_elapsed(self) -> float:
        """Get elapsed time in current phase."""
        return time.time() - self.phase_start_time

    @property
    def total_llm_time(self) -> float:
        """Aggregate LLM time across all agents."""
        return sum(agent.total_llm_time for agent in self.agents.values())

    @property
    def total_tool_time(self) -> float:
        """Aggregate tool time across all agents."""
        return sum(agent.total_tool_time for agent in self.agents.values())

    @property
    def total_llm_calls(self) -> int:
        """Total number of LLM calls across all agents."""
        return sum(agent.llm_call_count for agent in self.agents.values())

    def set_phase(self, phase: Literal["idle", "thinking", "executing", "waiting"], operation: Optional[str] = None):
        """Update the current phase and reset phase timer."""
        self.current_phase = phase
        self.phase_start_time = time.time()
        self.current_operation = operation

    def get_agent(self, name: str) -> AgentState:
        # Check if agent exists by name
        for agent in self.agents.values():
            if agent.name == name:
                return agent

        # Create new agent if not found
        agent_id = str(uuid.uuid4())
        agent = AgentState(agent_id=agent_id, name=name)
        self.agents[agent_id] = agent
        return agent

    def set_active_agent(self, name: str) -> AgentState:
        agent = self.get_agent(name)

        # Set previous active agent to idle
        if self.active_agent_id and self.active_agent_id != agent.agent_id:
            prev_agent = self.agents.get(self.active_agent_id)
            if prev_agent and prev_agent.status != "complete":
                prev_agent.status = "idle"

        self.active_agent_id = agent.agent_id
        if agent.status == "idle":
            agent.status = "thinking"
        return agent

    @property
    def duration(self) -> float:
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
