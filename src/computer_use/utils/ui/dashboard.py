"""
Main dashboard manager - orchestrates all UI components.
Real-time, immediate output with proper visual hierarchy.

Uses Rich renderers for consistent formatting and animations for feedback.
"""

import sys
import time
import threading
import uuid
from typing import Any, Dict, List, Optional, Set

from rich.console import Console
from rich.status import Status
from rich.text import Text

from .state import TaskState, AgentState, ToolState, VerbosityLevel, ActionType
from .theme import THEME, ICONS
from .renderers import (
    AgentRenderer,
    ToolRenderer,
    ThinkingRenderer,
    StatusBarRenderer,
)


class LogBatcher:
    """Batch log entries to reduce UI updates."""

    def __init__(self, batch_size: int = 10, timeout_sec: float = 0.2):
        self._batch: List[tuple] = []
        self._lock = threading.Lock()
        self._timer: Optional[threading.Timer] = None
        self._batch_size = batch_size
        self._timeout_sec = timeout_sec

    def add(
        self,
        action_type: ActionType,
        message: str,
        target: Optional[str] = None,
        status: str = "pending",
    ) -> None:
        with self._lock:
            self._batch.append((action_type, message, target, status))
            if len(self._batch) >= self._batch_size:
                self._flush_locked()
            elif self._timer is None:
                self._timer = threading.Timer(self._timeout_sec, self._flush)
                self._timer.start()

    def _flush(self) -> None:
        with self._lock:
            self._flush_locked()

    def _flush_locked(self) -> None:
        if not self._batch:
            return

        count = len(self._batch)
        last = self._batch[-1]
        action_type, message, target, status = last

        if count > 1:
            message = f"{message} (+{count - 1} more)"

        dashboard.add_log_entry(action_type, message, target, status)
        self._batch.clear()

        if self._timer:
            self._timer.cancel()
            self._timer = None

    def flush_now(self) -> None:
        self._flush()


class DashboardManager:
    """
    High-performance singleton dashboard manager.
    Real-time output with immediate flushing.
    """

    _instance: Optional["DashboardManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "DashboardManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        self.console = Console(force_terminal=True, force_interactive=False)
        self.verbosity = VerbosityLevel.NORMAL

        # Current task state
        self._task: Optional[TaskState] = None
        self._is_running = False

        # Renderers - use these for consistent formatting
        self._agent_renderer = AgentRenderer(self.console, self.verbosity)
        self._tool_renderer = ToolRenderer(self.console, self.verbosity)
        self._thinking_renderer = ThinkingRenderer(self.console, self.verbosity)
        self._status_renderer = StatusBarRenderer(self.console, self.verbosity)

        # Track what's been printed (avoid duplicates)
        self._printed_agents: Set[str] = set()
        self._printed_tools: Set[str] = set()
        self._started_tools: Set[str] = set()
        self._nested_tools: Set[str] = set()
        self._last_thought_hash: Optional[int] = None
        self._header_printed = False
        self._current_agent_name: Optional[str] = None
        self._current_status_message: str = ""
        self._pending_thought: Optional[str] = None
        self._pending_thought_agent_id: Optional[str] = None

        # Tool history for explorer
        self._tool_history: List[Dict[str, Any]] = []

        # Rich Status for animated spinner between actions
        self._status: Optional[Status] = None
        self._current_status_text: str = ""
        self._status_timer: Optional[threading.Timer] = None
        self._status_lock = threading.Lock()

    def _flush(self) -> None:
        """Force flush output to terminal immediately."""
        sys.stdout.flush()
        sys.stderr.flush()

    def _print(self, text: Text) -> None:
        """Print with immediate flush, pausing status spinner."""
        with self._status_lock:
            if self._status:
                try:
                    self._status.stop()
                except Exception:
                    pass
                self._status = None
        self.console.print(text)
        self._flush()

    def _print_raw(self, content: str) -> None:
        """Print raw string with immediate flush, pausing status spinner."""
        with self._status_lock:
            if self._status:
                try:
                    self._status.stop()
                except Exception:
                    pass
                self._status = None
        self.console.print(content)
        self._flush()

    @property
    def is_quiet(self) -> bool:
        return self.verbosity == VerbosityLevel.QUIET

    @property
    def is_verbose(self) -> bool:
        return self.verbosity == VerbosityLevel.VERBOSE

    def set_verbosity(self, level: VerbosityLevel) -> None:
        self.verbosity = level

    # ─────────────────────────────────────────────────────────────────────
    # Task lifecycle
    # ─────────────────────────────────────────────────────────────────────

    def set_task(self, description: str) -> None:
        """Initialize a new task. Fully reset all state from previous task."""
        self._stop_status_timer()
        self._stop_live_status()
        self._is_running = False

        self._task = TaskState(
            task_id=str(uuid.uuid4()),
            description=description,
            status="running",
        )
        self._printed_agents.clear()
        self._printed_tools.clear()
        self._started_tools.clear()
        self._nested_tools.clear()
        self._last_thought_hash = None
        self._header_printed = False
        self._current_agent_name = None
        self._current_status_message = ""
        self._pending_thought = None
        self._pending_thought_agent_id = None
        self._tool_history.clear()

    def start_dashboard(self) -> None:
        """Start the dashboard display."""
        if self.is_quiet or self._is_running:
            return

        self._is_running = True
        self._print_task_header()
        self._start_live_status()

    def stop_dashboard(self, print_log: bool = True, cancelled: bool = False) -> None:
        """Stop the dashboard and optionally print summary."""
        self._is_running = False
        self._stop_status_timer()
        self._stop_live_status()
        self._current_status_message = ""

        if self._task and self._task.active_agent_id and not cancelled:
            final_agent = self._task.agents.get(self._task.active_agent_id)
            if final_agent and final_agent.tools:
                if (
                    self._pending_thought
                    and self._pending_thought_agent_id == final_agent.agent_id
                ):
                    self._print_thought_full(self._pending_thought)
                    self._pending_thought = None
                    self._pending_thought_agent_id = None
                self._print_agent_summary(final_agent)

        if print_log and self._task and not cancelled:
            self.console.print()
            self.print_session_log()

    def complete_task(self, success: bool = True) -> None:
        """Mark the current task as complete."""
        if self._task:
            self._task.status = "complete" if success else "error"
            self._task.end_time = time.time()

    # ─────────────────────────────────────────────────────────────────────
    # Agent API
    # ─────────────────────────────────────────────────────────────────────

    def get_current_agent_name(self) -> str:
        """Get the name of the currently active agent."""
        return self._current_agent_name or ""

    def log_llm_start(self, model: str) -> Optional[str]:
        """
        Log the start of an LLM call for timing tracking.

        Args:
            model: Name of the LLM model being called.

        Returns:
            call_id for the LLM call, or None if no active agent.
        """
        if not self._task or not self._task.active_agent_id:
            return None

        agent = self._task.agents.get(self._task.active_agent_id)
        if not agent:
            return None

        llm_call = agent.start_llm_call(model)
        self._task.set_phase("thinking", model)
        return llm_call.call_id

    def log_llm_complete(
        self, prompt_tokens: int = 0, completion_tokens: int = 0
    ) -> None:
        """
        Log the completion of an LLM call.

        Args:
            prompt_tokens: Number of input tokens used.
            completion_tokens: Number of output tokens generated.
        """
        if not self._task or not self._task.active_agent_id:
            return

        agent = self._task.agents.get(self._task.active_agent_id)
        if agent:
            agent.complete_llm_call(prompt_tokens, completion_tokens)
        self._task.set_phase("executing")

    def get_current_llm_elapsed(self) -> Optional[float]:
        """
        Get elapsed time of the currently active LLM call.

        Returns:
            Elapsed time in seconds, or None if no active LLM call.
        """
        if not self._task or not self._task.active_agent_id:
            return None

        agent = self._task.agents.get(self._task.active_agent_id)
        if not agent:
            return None

        llm_call = agent.get_active_llm_call()
        if llm_call:
            return llm_call.elapsed
        return None

    def is_llm_active(self) -> bool:
        """Check if an LLM call is currently in progress."""
        if not self._task or not self._task.active_agent_id:
            return False

        agent = self._task.agents.get(self._task.active_agent_id)
        if not agent:
            return False

        return agent.get_active_llm_call() is not None

    def set_phase(self, phase: str, operation: Optional[str] = None) -> None:
        """
        Set the current execution phase.

        Args:
            phase: One of "idle", "thinking", "executing", "waiting"
            operation: Optional description of current operation
        """
        if self._task:
            self._task.set_phase(phase, operation)

    def set_agent(self, agent_name: str) -> None:
        """Set the active agent. Only prints header once per agent."""
        if not self._task:
            return

        agent_name = agent_name.strip()

        manager_names = {"Manager", "Task Orchestration Manager"}
        if agent_name in manager_names:
            agent_name = "Manager"

        if agent_name == self._current_agent_name:
            return

        was_manager = self._current_agent_name == "Manager"

        if self._current_agent_name and self._task.active_agent_id:
            prev_agent = self._task.agents.get(self._task.active_agent_id)
            if prev_agent:
                if (
                    self._pending_thought
                    and self._pending_thought_agent_id == prev_agent.agent_id
                ):
                    self._print_thought_full(self._pending_thought)
                    self._pending_thought = None
                    self._pending_thought_agent_id = None
                if was_manager and agent_name != "Manager":
                    self._print_delegation(agent_name)
                self._print_agent_summary(prev_agent)

        self._current_agent_name = agent_name
        self._last_thought_hash = None
        self._pending_thought = None
        self._pending_thought_agent_id = None
        agent = self._task.set_active_agent(agent_name)

        if agent.agent_id not in self._printed_agents:
            self._printed_agents.add(agent.agent_id)
            self._print_agent_header(agent)
            self._show_status(f"{agent_name} analyzing...")

    def set_thinking(self, thought: str) -> None:
        """Set current agent's thinking/reasoning. Shows FULL text."""
        if not self._task or not self._task.active_agent_id:
            return

        if not thought or not thought.strip():
            return

        thought = thought.strip()

        if self._is_system_prompt_leak(thought):
            return

        thought_hash = hash(thought[:100])
        if thought_hash == self._last_thought_hash:
            return
        self._last_thought_hash = thought_hash

        agent = self._task.agents.get(self._task.active_agent_id)
        if agent:
            agent.current_thought = thought
            agent.status = "thinking"
            self._pending_thought = thought
            self._pending_thought_agent_id = agent.agent_id
            short_thought = thought[:60] + "..." if len(thought) > 60 else thought
            self._show_status(short_thought)

    def _nest_tool_line(self, line: Text) -> Text:
        """Nest a tool-rendered line under a thought group."""
        nested = Text()
        nested.append("│   ", style="#3d444d")
        nested.append_text(line)
        return nested

    def _is_system_prompt_leak(self, text: str) -> bool:
        """Check if text is a system prompt leak that should be filtered."""
        leak_patterns = [
            "Tool Name:",
            "Tool Arguments:",
            "Tool Description:",
            "IMPORTANT: Use the following format",
            "you should always think about what to do",
            "You ONLY have access to the following tools",
        ]
        return any(pattern in text for pattern in leak_patterns)

    def set_action(self, action: str, target: Optional[str] = None) -> None:
        """Set current action description."""
        if not self._task or not self._task.active_agent_id:
            return

        agent = self._task.agents.get(self._task.active_agent_id)
        if agent:
            agent.status = "executing"

    def clear_action(self) -> None:
        """Clear the current action."""
        pass

    def log_delegation(self, agent_name: str, task_summary: str) -> None:
        """
        Log Manager's delegation to a specialist agent.

        Prints a clear delegation line before agent switch.
        """
        if not self._task:
            return

        line = Text()
        line.append("  → ", style=f"bold {THEME['agent_active']}")
        line.append("Delegating to ", style=THEME["muted"])
        line.append(agent_name, style=f"bold {THEME['agent_active']}")
        line.append(": ", style=THEME["muted"])

        if len(task_summary) > 80:
            task_summary = task_summary[:77] + "..."
        line.append(task_summary, style=THEME["text"])

        self._print(line)

    # ─────────────────────────────────────────────────────────────────────
    # Tool API
    # ─────────────────────────────────────────────────────────────────────

    def log_tool_start(self, tool_name: str, tool_input: Any) -> str:
        """Log tool execution start - prints immediately."""
        if not self._task or not self._task.active_agent_id:
            return ""

        if self._current_agent_name == "Manager":
            return ""

        agent = self._task.agents.get(self._task.active_agent_id)
        if not agent:
            return ""

        tool = agent.add_tool(tool_name, tool_input)
        self._task.total_tools += 1

        # Store in history for explorer
        self._tool_history.append(
            {
                "id": tool.tool_id,
                "name": tool_name,
                "input": tool_input,
                "output": None,
                "error": None,
                "status": "pending",
                "timestamp": time.time(),
            }
        )

        # Print immediately
        self._print_tool_start(tool)
        return tool.tool_id

    def get_pending_tool_id(self, tool_name: str = None) -> Optional[str]:
        """Find the most recent pending tool."""
        if not self._task or not self._task.active_agent_id:
            return None

        agent = self._task.agents.get(self._task.active_agent_id)
        if not agent:
            return None

        for tool in reversed(agent.tools):
            if tool.status == "pending":
                if tool_name is None or tool.name == tool_name:
                    return tool.tool_id

        return None

    def reset_tool_timer(self, tool_name: str = None) -> None:
        """Reset the start time of the most recent pending tool (call after approval)."""
        if not self._task or not self._task.active_agent_id:
            return

        agent = self._task.agents.get(self._task.active_agent_id)
        if not agent:
            return

        for tool in reversed(agent.tools):
            if tool.status == "pending":
                if tool_name is None or tool.name == tool_name:
                    tool.start_time = time.time()
                    return

    def log_tool_complete(
        self,
        tool_id: str,
        success: bool,
        action_taken: str = "",
        method_used: str = "",
        confidence: float = 0.0,
        error: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log tool completion - prints immediately."""
        if not self._task:
            return

        tool = None

        for agent in self._task.agents.values():
            tool = agent.get_tool(tool_id)
            if tool:
                break

        if not tool:
            for agent in self._task.agents.values():
                for t in reversed(agent.tools):
                    if t.status == "pending":
                        tool = t
                        break
                if tool:
                    break

        if not tool:
            return

        output = (
            action_taken
            or data
            or (f"method={method_used}" if method_used else "success")
        )
        tool.complete(success, output, error)

        if not success:
            self._task.failed_tools += 1

        for hist in self._tool_history:
            if hist["id"] == tool.tool_id:
                hist["output"] = output
                hist["error"] = error
                hist["status"] = "success" if success else "error"
                break

        self._print_tool_complete(tool)

    # ─────────────────────────────────────────────────────────────────────
    # Token usage
    # ─────────────────────────────────────────────────────────────────────

    def update_token_usage(self, input_tokens: int, output_tokens: int) -> None:
        """Update token usage counters."""
        if self._task:
            self._task.token_input = input_tokens
            self._task.token_output = output_tokens

    # ─────────────────────────────────────────────────────────────────────
    # Printing methods - REAL TIME
    # ─────────────────────────────────────────────────────────────────────

    def _print_task_header(self) -> None:
        """Print HUD-style task header."""
        if self._header_printed or not self._task:
            return
        self._header_printed = True

        c_border = "#3d444d"
        c_muted = "#484f58"
        c_text = "#c9d1d9"
        c_highlight = "#58a6ff"
        w = self.console.width

        self.console.print()
        self._print_raw(f"[{c_border}]╭{'─' * (w - 2)}╮[/]")

        label = "MISSION"
        desc = (
            self._task.description[: w - 20]
            if len(self._task.description) > w - 20
            else self._task.description
        )
        inner = w - 4
        content = f"[{c_muted}]{label}:[/] [{c_text}]{desc}[/]"
        pad = inner - len(label) - len(desc) - 2
        self._print_raw(
            f"[{c_border}]│[/] {content}{' ' * max(1, pad)} [{c_border}]│[/]"
        )

        self._print_raw(f"[{c_border}]├{'─' * (w - 2)}┤[/]")

        status_content = f"[{c_highlight}]●[/] [{c_muted}]EXECUTING[/]"
        status_pad = inner - 12
        self._print_raw(
            f"[{c_border}]│[/] {status_content}{' ' * status_pad} [{c_border}]│[/]"
        )

        self._print_raw(f"[{c_border}]╰{'─' * (w - 2)}╯[/]")
        self.console.print()
        self.console.print()
        self._flush()

    def _print_delegation(self, target_agent: str) -> None:
        """Print delegation message when Manager delegates to another agent."""
        line = Text()
        line.append("\n  → ", style=f"bold {THEME['agent_active']}")
        line.append("Delegating to ", style=THEME["muted"])
        line.append(target_agent, style=f"bold {THEME['agent_active']}")
        self._print(line)

    def _print_agent_summary(self, agent: AgentState) -> None:
        """Print HUD-style agent completion summary."""
        c_border = "#3d444d"
        c_success = "#3fb950"
        c_dim = "#8b949e"
        c_text = "#c9d1d9"

        self.console.print()

        duration = agent.duration
        if duration < 60:
            duration_str = f"{int(duration)}s"
        else:
            mins = int(duration // 60)
            secs = int(duration % 60)
            duration_str = f"{mins}m{secs:02d}s"

        total_tools = len(agent.tools)
        success_tools = sum(1 for t in agent.tools if t.status == "success")

        summary = Text()
        summary.append("╰─ ", style=c_border)
        summary.append("● ", style=c_success)
        summary.append(agent.name.upper(), style=f"bold {c_text}")
        summary.append(" ─ ", style=c_border)
        summary.append("COMPLETE", style=f"bold {c_success}")
        summary.append("  │  ", style=c_border)
        summary.append(f"T+{duration_str}", style=c_dim)
        summary.append("  │  ", style=c_border)
        summary.append(f"OPS:{success_tools}/{total_tools}", style=c_dim)

        self._print(summary)
        self.console.print()
        self.console.print()

    def _print_agent_header(self, agent: AgentState) -> None:
        """Print HUD-style agent header when it becomes active."""
        c_border = "#3d444d"
        c_active = "#58a6ff"
        c_text = "#c9d1d9"

        w = self.console.width
        name = agent.name.upper()
        status = "ACTIVE"

        self.console.print()
        self.console.print()
        self._print_raw(f"[{c_border}]╭{'─' * (w - 2)}╮[/]")

        inner = w - 4
        left = f"[{c_active}]●[/] [{c_text}]{name}[/]"
        right = f"[{c_active}]{status}[/]"
        left_len = len(name) + 2
        right_len = len(status)
        pad = inner - left_len - right_len
        self._print_raw(f"[{c_border}]│[/] {left}{' ' * pad}{right} [{c_border}]│[/]")

        self._print_raw(f"[{c_border}]╰{'─' * (w - 2)}╯[/]")
        self.console.print()

    def _print_thought_full(self, thought: str) -> None:
        """Print FULL thinking/reasoning using ThinkingRenderer."""
        thought = thought.strip()
        if not thought:
            return

        self.console.print()
        thought_line = self._thinking_renderer.render_inline(thought)
        self._print(thought_line)

    def _print_tool_start(self, tool: ToolState) -> None:
        """Print tool start using the ToolRenderer, then show waiting status."""
        if tool.tool_id in self._started_tools:
            return

        self._started_tools.add(tool.tool_id)

        is_nested = False
        if (
            self._pending_thought
            and self._pending_thought_agent_id
            and self._task
            and self._task.active_agent_id
        ):
            active_agent = self._task.agents.get(self._task.active_agent_id)
            if active_agent and active_agent.agent_id == self._pending_thought_agent_id:
                self._print_thought_full(self._pending_thought)
                self._pending_thought = None
                self._pending_thought_agent_id = None
                self._nested_tools.add(tool.tool_id)
                is_nested = True

        if not is_nested:
            action_desc = self._get_action_description(tool.name, tool.input_data)
            if action_desc:
                action_line = Text()
                action_line.append(
                    f"  {ICONS['bullet']} ", style=f"bold {THEME['tool_pending']}"
                )
                action_line.append(action_desc, style=f"italic {THEME['text']}")
                self._print(action_line)

        pending_line = Text()
        pending_line.append("├─ ", style="#3d444d")
        pending_line.append("⟳ ", style=THEME["tool_pending"])
        pending_line.append(tool.name, style=f"bold {THEME['text']}")
        self._print(self._nest_tool_line(pending_line) if is_nested else pending_line)

        self._show_status(f"Running {tool.name}...")

    def _get_action_description(self, tool_name: str, input_data: Dict) -> str:
        """
        Generate human-readable action description.
        Prioritizes agent's explanation if available.
        """
        if not input_data:
            return ""

        import json

        data = input_data.get("value", input_data)
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                data = {"value": data}

        if isinstance(data, list) and len(data) > 0:
            data = data[0] if isinstance(data[0], dict) else {"value": data}

        explanation = None
        if isinstance(data, dict):
            explanation = data.get("explanation")

        if explanation and isinstance(explanation, str) and len(explanation) > 5:
            return explanation[:120] + ("..." if len(explanation) > 120 else "")

        action_map = {
            "open_application": lambda d: f"Opening {d.get('app_name', 'application')}",
            "check_app_running": lambda d: f"Checking if {d.get('app_name', 'app')} is running",
            "click_element": lambda d: f"Clicking {d.get('target', d.get('element_id', 'element'))}",
            "type_text": lambda d: f"Typing text into {d.get('target', 'field')}",
            "read_screen_text": lambda d: f"Reading text from {d.get('app_name', 'screen')}",
            "get_accessible_elements": lambda d: f"Scanning {d.get('app_name', 'app')} UI",
            "take_screenshot": lambda d: "Taking screenshot",
            "scroll": lambda d: f"Scrolling {d.get('direction', 'down')}",
            "web_automation": lambda d: d.get("task", "Running web automation")[:80],
            "execute_shell_command": lambda d: "Executing command",
            "human_assistance": lambda d: f"⚠️ {d.get('reason', 'Requesting human help')}",
            "request_human_assistance": lambda d: f"⚠️ {d.get('reason', 'Requesting human help')}",
            "request_human_input": lambda d: f"⚠️ {d.get('prompt', 'Requesting input')}",
            "delegate_task": lambda d: f"Delegating to {d.get('agent', 'agent')}",
            "coding_task": lambda d: d.get("task", "Running coding task")[:80],
        }

        if tool_name in action_map:
            try:
                return action_map[tool_name](data)
            except Exception:
                pass

        return ""

    def _print_tool_complete(self, tool: ToolState) -> None:
        """
        Print tool completion with duration in header.

        Format:
          ✓ tool_name (5.00s)
              ← output
        """
        self._stop_live_status()
        is_nested = tool.tool_id in self._nested_tools
        if tool.tool_id not in self._printed_tools:
            header = self._tool_renderer._render_tool_header(tool)
            self._print(self._nest_tool_line(header) if is_nested else header)
            if tool.input_data:
                input_line = self._tool_renderer._render_input(tool.input_data)
                self._print(
                    self._nest_tool_line(input_line) if is_nested else input_line
                )
            self._printed_tools.add(tool.tool_id)

        if tool.status == "success":
            output_line = self._tool_renderer._render_output(
                tool.output_data, tool.duration
            )
            self._print(self._nest_tool_line(output_line) if is_nested else output_line)
            self.console.print()
            self._show_status("Processing results...")
        else:
            error_line = self._tool_renderer._render_error(
                tool.error or "Unknown error", tool.duration
            )
            self._print(self._nest_tool_line(error_line) if is_nested else error_line)
            self.console.print()
            self._show_status("Handling error...")
        self._started_tools.discard(tool.tool_id)
        if is_nested:
            self._nested_tools.discard(tool.tool_id)

    # ─────────────────────────────────────────────────────────────────────
    # Live status with Rich spinner (inline, not sticky)
    # ─────────────────────────────────────────────────────────────────────

    def _start_live_status(self) -> None:
        """Start the Rich Status spinner with initial message."""
        self._show_status("Initializing...")

    def _stop_live_status(self) -> None:
        """Stop and clear any active status spinner."""
        self._stop_status_timer()
        with self._status_lock:
            if self._status:
                try:
                    self._status.stop()
                except Exception:
                    pass
                self._status = None
            self._current_status_message = ""

    def _get_refresh_interval(self) -> float:
        """
        Get adaptive refresh interval based on current phase.

        Returns:
            0.25s (4Hz) during active operations, 1.0s (1Hz) when idle.
        """
        if self._task and self._task.current_phase in ("thinking", "executing"):
            return 0.25
        return 1.0

    def _start_status_timer(self) -> None:
        """Start timer to refresh status bar with adaptive rate."""
        self._stop_status_timer()
        if not self._is_running:
            return

        def refresh() -> None:
            if not self._is_running:
                return
            with self._status_lock:
                if self._status and self._task:
                    try:
                        self._status.update(self._build_status_line())
                    except Exception:
                        pass
            if self._is_running:
                self._start_status_timer()

        interval = self._get_refresh_interval()
        self._status_timer = threading.Timer(interval, refresh)
        self._status_timer.daemon = True
        self._status_timer.start()

    def _stop_status_timer(self) -> None:
        """Stop the status refresh timer."""
        if self._status_timer:
            self._status_timer.cancel()
            self._status_timer = None

    def _show_status(self, message: str = "") -> None:
        """Show animated status with Rich spinner inline using dedicated console."""
        if not self._is_running or not self._task:
            return

        self._current_status_message = message
        status_text = self._build_status_line(message)

        with self._status_lock:
            if self._status:
                try:
                    self._status.update(status_text)
                except Exception:
                    pass
            else:
                status_console = Console(force_terminal=True)
                self._status = Status(
                    status_text,
                    spinner="dots",
                    spinner_style=THEME["agent_active"],
                    console=status_console,
                    refresh_per_second=4,
                )
                self._status.start()
                self._start_status_timer()

    def _build_status_line(self, message: str = "") -> str:
        """
        Build clean status line with phase, agent, timing, and tokens.

        Format: ├─ ◐ THINKING │ AGENT │ T+Xs │ Nk↑ Nk↓ │ ESC cancel
        """
        c_border = "#3d444d"
        c_active = "#58a6ff"
        c_dim = "#8b949e"
        c_muted = "#484f58"
        c_thinking = "#aaaaff"
        c_executing = "#ffaa00"

        if not self._task:
            return ""

        elapsed = time.time() - self._task.start_time
        if elapsed < 60:
            time_str = f"{int(elapsed)}s"
        else:
            time_str = f"{int(elapsed // 60)}m{int(elapsed % 60):02d}s"

        tokens_in = self._task.token_input
        tokens_out = self._task.token_output
        if tokens_in >= 1000:
            tokens_in_str = f"{tokens_in / 1000:.1f}k"
        else:
            tokens_in_str = str(tokens_in)
        if tokens_out >= 1000:
            tokens_out_str = f"{tokens_out / 1000:.1f}k"
        else:
            tokens_out_str = str(tokens_out)

        agent_name = (self._current_agent_name or "Agent").upper()

        phase = self._task.current_phase

        phase_config = {
            "thinking": ("THINKING", c_thinking, "◐"),
            "executing": ("RUNNING", c_executing, "⚙"),
            "waiting": ("IDLE", c_muted, "○"),
            "idle": ("IDLE", c_muted, "○"),
        }
        label, color, icon = phase_config.get(phase, ("IDLE", c_muted, "○"))

        sep = f"[{c_border}]│[/]"

        return (
            f"\n[{c_border}]├─[/] [{color}]{icon} {label}[/]  {sep}  "
            f"[{c_active}]{agent_name}[/]  {sep}  "
            f"[{c_dim}]T+{time_str}[/]  {sep}  "
            f"[{c_dim}]{tokens_in_str}↑ {tokens_out_str}↓[/]  {sep}  "
            f"[{c_muted}]ESC[/] [{c_dim}]cancel[/]"
        )

    def _print_status_bar(self) -> None:
        """Print inline status bar (matches TASK header style)."""
        if not self._task:
            return

        elapsed = self._task.duration
        if elapsed < 60:
            time_str = f"{int(elapsed)}s"
        else:
            time_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s"

        tokens_in = self._task.token_input
        tokens_out = self._task.token_output

        agent_name = self._current_agent_name or "Starting"

        agent_tools = "0/0"
        if self._task.active_agent_id:
            agent = self._task.agents.get(self._task.active_agent_id)
            if agent:
                total = len(agent.tools)
                done = sum(1 for t in agent.tools if t.status != "pending")
                agent_tools = f"{done}/{total}"

        total_tools = self._task.total_tools
        global_done = sum(
            1
            for a in self._task.agents.values()
            for t in a.tools
            if t.status != "pending"
        )

        bar = Text()
        bar.append(
            "  ─────────────────────────────────────────────────────────────────\n",
            style=THEME["border"],
        )
        bar.append(f"  {agent_name} ", style=f"bold {THEME['agent_active']}")
        bar.append(f"[{agent_tools}]", style=THEME["muted"])
        bar.append(" │ ", style=THEME["border"])
        bar.append(f"t:{time_str}", style=THEME["muted"])
        bar.append(" │ ", style=THEME["border"])
        bar.append(f"tools:{global_done}/{total_tools}", style=THEME["muted"])
        bar.append(" │ ", style=THEME["border"])
        bar.append(f"tok:{tokens_in}↑{tokens_out}↓", style=THEME["muted"])
        bar.append(
            "\n  ─────────────────────────────────────────────────────────────────",
            style=THEME["border"],
        )

        self.console.print(bar)
        self._flush()

    def _build_status_message(self) -> str:
        """Build the current status message for the spinner."""
        if not self._task:
            return "Initializing..."

        parts = []

        if self._current_agent_name:
            parts.append(f"[bold {THEME['agent_active']}]{self._current_agent_name}[/]")

        agent = None
        if self._task.active_agent_id:
            agent = self._task.agents.get(self._task.active_agent_id)

        if agent:
            pending_tools = [t for t in agent.tools if t.status == "pending"]
            if pending_tools:
                tool = pending_tools[-1]
                parts.append(f"[{THEME['tool_pending']}]⚙ {tool.name}[/]")
            elif agent.status == "thinking":
                parts.append(f"[{THEME['thinking']}]💭 Thinking[/]")
            else:
                parts.append(f"[{THEME['muted']}]Processing[/]")

        elapsed = self._task.duration
        if elapsed < 60:
            time_str = f"{int(elapsed)}s"
        else:
            time_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s"
        parts.append(f"[{THEME['muted']}]{time_str}[/]")

        if self._task.token_input > 0 or self._task.token_output > 0:
            tokens = f"{self._task.token_input}↑ {self._task.token_output}↓"
            parts.append(f"[{THEME['muted']}]{tokens}[/]")

        return " │ ".join(parts) if parts else "Processing..."

    def _render_status_line(self) -> None:
        """Update the live status line."""
        self._update_live_status()

    # ─────────────────────────────────────────────────────────────────────
    # Session log
    # ─────────────────────────────────────────────────────────────────────

    def print_session_log(self) -> None:
        """Print the complete session summary with timing breakdown."""
        if not self._task:
            return

        self._print_raw(f"\n[{THEME['border']}]{'═' * 70}[/]")
        self._print_raw(f"[bold {THEME['text']}]  SESSION SUMMARY[/]")
        self._print_raw(f"[{THEME['border']}]{'═' * 70}[/]")

        duration = self._task.duration
        if duration < 60:
            duration_str = f"{int(duration)}s"
        else:
            mins = int(duration // 60)
            secs = int(duration % 60)
            duration_str = f"{mins}m {secs}s"

        success = self._task.total_tools - self._task.failed_tools
        stats = (
            f"  Duration: {duration_str} │ "
            f"Tools: {success}/{self._task.total_tools} │ "
            f"Tokens: {self._task.token_input}↑ {self._task.token_output}↓ │ "
            f"Agents: {len(self._task.agents)}"
        )
        self._print_raw(f"[{THEME['muted']}]{stats}[/]")

        llm_time = self._task.total_llm_time
        tool_time = self._task.total_tool_time
        total_tracked = llm_time + tool_time
        other_time = max(0, duration - total_tracked)

        if total_tracked > 0:
            llm_pct = (llm_time / duration * 100) if duration > 0 else 0
            tool_pct = (tool_time / duration * 100) if duration > 0 else 0
            other_pct = (other_time / duration * 100) if duration > 0 else 0

            def fmt_time(t: float) -> str:
                if t < 1:
                    return f"{t:.1f}s"
                elif t < 60:
                    return f"{int(t)}s"
                return f"{int(t // 60)}m {int(t % 60)}s"

            timing_stats = (
                f"  Time Breakdown: "
                f"LLM {fmt_time(llm_time)} ({llm_pct:.0f}%) │ "
                f"Tools {fmt_time(tool_time)} ({tool_pct:.0f}%) │ "
                f"Other {fmt_time(other_time)} ({other_pct:.0f}%) │ "
                f"LLM Calls: {self._task.total_llm_calls}"
            )
            self._print_raw(f"[{THEME['muted']}]{timing_stats}[/]")

        self._print_raw(f"[{THEME['border']}]{'═' * 70}[/]")

        if self._task.agents:
            self._print_raw(f"[bold {THEME['text']}]  AGENT BREAKDOWN[/]")
            self._print_raw(f"[{THEME['border']}]{'─' * 70}[/]")

            for agent in self._task.agents.values():
                agent_llm = agent.total_llm_time
                agent_tool = agent.total_tool_time
                agent_calls = agent.llm_call_count
                tool_count = len(
                    [t for t in agent.tools if t.status in ("success", "error")]
                )

                def fmt_time(t: float) -> str:
                    if t < 1:
                        return f"{t:.1f}s"
                    elif t < 60:
                        return f"{int(t)}s"
                    return f"{int(t // 60)}m {int(t % 60)}s"

                agent_line = (
                    f"  {agent.name:<14} │ "
                    f"{fmt_time(agent.duration):>6} │ "
                    f"LLM: {fmt_time(agent_llm):>5} ({agent_calls} calls) │ "
                    f"Tools: {fmt_time(agent_tool):>5} ({tool_count} calls)"
                )
                self._print_raw(f"[{THEME['muted']}]{agent_line}[/]")

            self._print_raw(f"[{THEME['border']}]{'═' * 70}[/]")

    # ─────────────────────────────────────────────────────────────────────
    # Tool explorer
    # ─────────────────────────────────────────────────────────────────────

    def start_tool_explorer(self) -> None:
        """Launch interactive tool explorer."""
        if not self._tool_history:
            self._print_raw(f"[{THEME['muted']}]No tools executed.[/]")
            return

        self.console.print()
        self._print_raw(f"[bold {THEME['text']}]─── Tool Explorer ───[/]")
        self._print_raw(
            f"[{THEME['muted']}]Enter tool number to expand, 'q' to quit[/]"
        )
        self.console.print()

        for idx, tool in enumerate(self._tool_history, 1):
            status_icon = (
                ICONS["success"] if tool["status"] == "success" else ICONS["error"]
            )
            status_color = (
                THEME["tool_success"] if tool["status"] == "success" else THEME["error"]
            )
            self._print_raw(
                f"  [{status_color}]{status_icon}[/] [{THEME['muted']}]{idx}.[/] "
                f"[bold {THEME['text']}]{tool['name']}[/]"
            )

        self.console.print()

        while True:
            try:
                choice = self.console.input(f"[{THEME['text']}]› [/]").strip().lower()
                if choice in ("q", "quit", "exit", ""):
                    break
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(self._tool_history):
                        self._print_tool_detail(self._tool_history[idx])
                    else:
                        self._print_raw(f"[{THEME['warning']}]Invalid number[/]")
            except (EOFError, KeyboardInterrupt):
                break

    def _print_tool_detail(self, tool: Dict[str, Any]) -> None:
        """Print expanded tool details."""
        import json

        self.console.print()
        self._print_raw(f"[bold {THEME['text']}]┌─ {tool['name']} ─┐[/]")

        self._print_raw(f"[{THEME['input']}]│ Input:[/]")
        if tool["input"]:
            try:
                formatted = json.dumps(tool["input"], indent=2, default=str)
                for line in formatted.split("\n"):
                    self._print_raw(f"[{THEME['muted']}]│   [/]{line}")
            except Exception:
                self._print_raw(f"[{THEME['muted']}]│   [/]{tool['input']}")
        else:
            self._print_raw(f"[{THEME['muted']}]│   (none)[/]")

        self._print_raw(f"[{THEME['output']}]│ Output:[/]")
        if tool["output"]:
            output_str = str(tool["output"])
            for line in output_str.split("\n"):
                self._print_raw(f"[{THEME['muted']}]│   [/]{line}")
        elif tool["error"]:
            self._print_raw(f"[{THEME['error']}]│   {tool['error']}[/]")
        else:
            self._print_raw(f"[{THEME['muted']}]│   (none)[/]")

        self._print_raw(f"[{THEME['border']}]└{'─' * 40}┘[/]")
        self.console.print()

    # ─────────────────────────────────────────────────────────────────────
    # Legacy API compatibility
    # ─────────────────────────────────────────────────────────────────────

    def add_log_entry(
        self,
        action_type: ActionType,
        message: str,
        target: Optional[str] = None,
        status: str = "pending",
    ) -> int:
        """Legacy API: Add a log entry."""
        if self._is_running:
            line = Text()
            if status == "error":
                line.append(f"  {ICONS['error']} ", style=f"bold {THEME['error']}")
                line.append(message, style=THEME["error"])
            else:
                line.append(f"  {ICONS['bullet']} ", style=THEME["muted"])
                line.append(message, style=THEME["text"])
            self._print(line)
        return 0

    def update_log_entry(self, idx: int, status: str) -> None:
        """Legacy API: Update a log entry status."""
        pass

    def set_steps(self, current: int, total: int) -> None:
        """Legacy API: Set step progress."""
        pass

    def set_last_result(self, result: str) -> None:
        """Legacy API: Set last result."""
        pass

    def show_human_assistance(self, reason: str, instructions: str) -> None:
        """Legacy API: Show human assistance panel."""
        pass

    def hide_human_assistance(self) -> None:
        """Legacy API: Hide human assistance panel."""
        pass

    def show_command_approval(self, command: str) -> None:
        """Legacy API: Show command approval panel."""
        pass

    def hide_command_approval(self) -> None:
        """Legacy API: Hide command approval panel."""
        pass

    def set_browser_session(self, active: bool, profile: Optional[str] = None) -> None:
        """
        Track browser session state.

        When active is True, marks that the browser agent has executed work.
        This is used to avoid false-positive hallucination detection.
        """
        if self._task and active:
            self._task.browser_agent_executed = True
            self._task.external_tools_executed = True

    def mark_external_tool_executed(self) -> None:
        """
        Mark that an external tool system has executed work.

        Used by tools that use their own sub-agents (browser-use, coding agents, etc.)
        to prevent false-positive hallucination detection when the main tool counter
        stays at 0 but real work was performed.
        """
        if self._task:
            self._task.external_tools_executed = True

    def has_external_work_executed(self) -> bool:
        """
        Check if any external tool system has executed work.

        Returns True if browser agent or other external tools performed work,
        even if the main tool counter is 0.
        """
        if not self._task:
            return False
        return self._task.external_tools_executed or self._task.browser_agent_executed

    def refresh(self) -> None:
        """Legacy API: Force refresh."""
        self._render_status_line()


# Singleton instance
dashboard = DashboardManager()
console = dashboard.console
