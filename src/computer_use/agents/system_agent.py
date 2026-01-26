"""
System agent that uses shell commands dynamically.
LLM generates commands iteratively based on output.
"""

from typing import Dict, Any, Optional
import subprocess
from pydantic import BaseModel, Field
from ..schemas.actions import ActionResult
from ..utils.ui import print_info, print_success, print_failure, console


class ShellCommand(BaseModel):
    """
    Shell command decision from LLM.
    """

    command: str = Field(
        description="Shell command to execute (e.g., 'ls ~/Documents')"
    )
    reasoning: str = Field(description="Why this command is needed")
    is_complete: bool = Field(default=False, description="Is the task fully complete?")
    needs_handoff: bool = Field(
        default=False, description="Does this need another agent (e.g., GUI)?"
    )
    handoff_agent: Optional[str] = Field(
        default=None, description="Which agent to handoff to: 'gui' or 'browser'"
    )
    handoff_reason: Optional[str] = Field(
        default=None, description="Why handoff is needed"
    )


class SystemAgent:
    """
    Shell-command driven system agent.
    Uses LLM to generate commands iteratively.
    """

    def __init__(self, tool_registry, safety_checker, llm_client=None):
        """
        Initialize system agent.

        Args:
            tool_registry: PlatformToolRegistry instance
            safety_checker: SafetyChecker for validating operations
            llm_client: LLM for generating shell commands
        """
        self.tool_registry = tool_registry
        self.safety_checker = safety_checker
        self.llm_client = llm_client
        self.max_steps = 10
        self.command_history = []

    async def execute_task(
        self, task: str, context: Dict[str, Any] = None
    ) -> ActionResult:
        """
        Execute task by generating shell commands iteratively.

        Args:
            task: Natural language task description
            context: Optional context from other agents (handoff info)

        Returns:
            ActionResult with task status
        """
        if not self.llm_client:
            return ActionResult(
                success=False,
                action_taken="No LLM available",
                method_used="system",
                confidence=0.0,
                error="System agent requires LLM",
            )

        handoff_context = context.get("handoff_context") if context else None
        confirmation_manager = context.get("confirmation_manager") if context else None
        previous_results = context.get("previous_results", []) if context else []

        if not confirmation_manager:
            return ActionResult(
                success=False,
                action_taken="No confirmation manager",
                method_used="system",
                confidence=0.0,
                error="System agent requires confirmation manager for safety",
            )

        if handoff_context:
            print_info("Received handoff from GUI agent")
            console.print(
                f"  [dim]Failed action: {handoff_context.get('failed_action')}[/dim]"
            )
            console.print("  [dim]Will use CLI instead...[/dim]\n")

        self.command_history = []
        step = 0
        task_complete = False
        last_output = ""

        print_info(f"Starting shell command loop (max {self.max_steps} steps)")

        while step < self.max_steps and not task_complete:
            step += 1

            if confirmation_manager.is_denied():
                return ActionResult(
                    success=False,
                    action_taken="User stopped agent",
                    method_used="system_shell",
                    confidence=0.0,
                    error="User denied command execution",
                )

            command_decision = await self._get_next_command(
                task, handoff_context, previous_results, last_output, step
            )

            console.print(f"\n[bold cyan]Step {step}:[/bold cyan]")
            console.print(f"  [dim]Reasoning: {command_decision.reasoning}[/dim]")

            if command_decision.needs_handoff:
                print_info(f"Requesting handoff to {command_decision.handoff_agent}")
                return ActionResult(
                    success=False,
                    action_taken=f"Needs {command_decision.handoff_agent} agent",
                    method_used="system_shell",
                    confidence=0.0,
                    handoff_requested=True,
                    suggested_agent=command_decision.handoff_agent,
                    handoff_reason=command_decision.handoff_reason,
                    handoff_context={
                        "original_task": task,
                        "system_progress": self.command_history,
                        "last_output": last_output,
                    },
                )

            command = command_decision.command

            if command:
                console.print(f"  [yellow]Command:[/yellow] [cyan]{command}[/cyan]")

                allowed, reason = confirmation_manager.request_confirmation(command)

                if not allowed:
                    return ActionResult(
                        success=False,
                        action_taken=f"Command denied: {command}",
                        method_used="system_shell",
                        confidence=0.0,
                        error=f"User {reason} command",
                    )

                result = self._execute_command(command)
                self.command_history.append(
                    {"command": command, "output": result.get("output", "")}
                )

                if not result["success"]:
                    print_failure(f"Failed: {result.get('error')}")
                    last_output = f"ERROR: {result.get('error')}"
                else:
                    output = result.get("output", "").strip()
                    if output:
                        from ..utils.ui.core.responsive import ResponsiveWidth

                        out_preview = ResponsiveWidth.truncate(
                            str(output), max_ratio=0.8, min_width=60
                        )
                        console.print(f"  [green]Output:[/green] {out_preview}")
                        last_output = output
                    else:
                        print_success("Success (no output)")
                        last_output = "Command succeeded"

            if command_decision.is_complete:
                print_success("Task complete")
                task_complete = True
                break

        if task_complete:
            return ActionResult(
                success=True,
                action_taken=f"Completed in {step} commands",
                method_used="system_shell",
                confidence=1.0,
                data={"commands": self.command_history},
            )
        else:
            return ActionResult(
                success=False,
                action_taken=f"Exceeded {self.max_steps} steps",
                method_used="system_shell",
                confidence=0.0,
                error="Task not completed within step limit",
            )

    async def _get_next_command(
        self,
        task: str,
        handoff_context: Optional[Dict],
        previous_results: list,
        last_output: str,
        step: int,
    ) -> ShellCommand:
        """
        Ask LLM for next shell command based on current state.

        Args:
            task: Original task
            handoff_context: Context from handoff
            previous_results: Results from previous agents (browser, GUI)
            last_output: Output from last command
            step: Current step number

        Returns:
            ShellCommand decision
        """
        prompt = f"""
You are a shell command agent. Generate ONE shell command at a time to accomplish the task.

TASK: {task}
"""

        if previous_results:
            prompt += "\n" + "=" * 60 + "\n"
            prompt += "PREVIOUS AGENT WORK (Use this information!):\n"
            prompt += "=" * 60 + "\n"

            for i, res in enumerate(previous_results, 1):
                agent_type = res.get("method_used", "unknown")
                action = res.get("action_taken", "")
                success = "✅" if res.get("success") else "❌"
                prompt += f"\n{success} Agent {i} ({agent_type}): {action}\n"

                if res.get("data"):
                    data = res.get("data", {})
                    output = data.get("output")

                    if isinstance(output, dict):
                        try:
                            from ..schemas.browser_output import BrowserOutput

                            browser_output = BrowserOutput(**output)
                            prompt += f"\n📝 Summary:\n{browser_output.text}\n"

                            if browser_output.has_files():
                                prompt += "\n📁 DOWNLOADED FILES (use these paths!):\n"
                                for file_path in browser_output.files:
                                    prompt += f"   • {file_path}\n"

                                prompt += "\n📊 File Details:\n"
                                for file_detail in browser_output.file_details:
                                    size_kb = file_detail.size / 1024
                                    prompt += (
                                        f"   • {file_detail.name} ({size_kb:.1f} KB)\n"
                                    )
                                    prompt += f"     Path: {file_detail.path}\n"
                        except Exception:
                            if output.get("text"):
                                prompt += f"\n📝 Summary:\n{output['text']}\n"
                            if output.get("files"):
                                prompt += "\n📁 Files:\n"
                                for file_path in output.get("files", []):
                                    prompt += f"   • {file_path}\n"

                    elif isinstance(output, str):
                        prompt += f"     Output: {output}\n"

            prompt += "\n" + "=" * 60 + "\n"
            prompt += "🎯 YOUR JOB: Use the files/data above in your commands!\n"
            prompt += "=" * 60 + "\n\n"

        if handoff_context:
            prompt += "\n" + "=" * 60 + "\n"
            prompt += "HANDOFF FROM GUI AGENT:\n"
            prompt += "=" * 60 + "\n"
            prompt += f"GUI agent tried: {handoff_context.get('failed_action')} → {handoff_context.get('failed_target')}\n"
            prompt += f"Current app: {handoff_context.get('current_app')}\n"
            prompt += f"Reason for handoff: {handoff_context.get('error', 'Element not found in GUI')}\n"
            prompt += "\n🎯 YOUR JOB: Complete this task using shell commands since GUI approach failed\n"
            prompt += "=" * 60 + "\n\n"

        if self.command_history:
            prompt += "\n" + "=" * 60 + "\n"
            prompt += "YOUR COMMAND HISTORY (What you've tried):\n"
            prompt += "=" * 60 + "\n"
            failed_commands = []
            successful_steps = []

            for i, cmd in enumerate(self.command_history[-5:], 1):
                success_marker = "✅" if cmd.get("success") else "❌"
                prompt += f"{success_marker} Step {i}: {cmd['command']}\n"

                if cmd.get("output"):
                    from ..utils.ui.core.responsive import ResponsiveWidth

                    output_preview = ResponsiveWidth.truncate(
                        str(cmd.get("output", "")).strip(), max_ratio=0.8, min_width=60
                    )
                    prompt += f"   Output: {output_preview}\n"

                if not cmd.get("success"):
                    failed_commands.append(cmd["command"])
                else:
                    successful_steps.append((cmd["command"], cmd.get("output", "")))

            if successful_steps:
                prompt += "\n✅ SUCCESSFUL STEPS - Build on these:\n"
                for cmd, output in successful_steps[-2:]:
                    prompt += f"   • {cmd}\n"
                    if output:
                        from ..utils.ui.core.responsive import ResponsiveWidth

                        prompt += f"     Result: {ResponsiveWidth.truncate(str(output).strip(), max_ratio=0.7, min_width=40)}\n"

            if failed_commands:
                prompt += "\n❌ FAILED COMMANDS - DO NOT REPEAT:\n"
                for failed_cmd in failed_commands:
                    prompt += f"   • {failed_cmd}\n"
                prompt += "\n💡 Try a DIFFERENT approach for what failed!\n"

            prompt += "=" * 60 + "\n"

        if last_output:
            prompt += f"\nLAST OUTPUT:\n{last_output}\n"

        prompt += f"""
STRATEGIC GUIDELINES:

1. WORKFLOW THINKING:
   - Analyze what you accomplished so far
   - If you found a file → copy/move/open it (progress!)
   - If command failed → try DIFFERENT approach (don't repeat!)
   - Sequence matters: find → copy → open (NOT: find → find → find)

2. LEARN FROM FAILURES:
   - Command not found? Use alternative commands
   - Permission denied? Try different approach
   - Path doesn't exist? Check what's available first

3. CROSS-PLATFORM COMMANDS:
   - List files: ls, find
   - Copy/move: cp, mv
   - Open files: Detect platform and use appropriate command
   - Random selection: Use available tools (head, tail, sort)
   - If tool doesn't exist, find alternatives!

4. PROBLEM-SOLVING:
   - Previous step succeeded? Build on it, don't redo it
   - Got output with file path? Use that path in next command
   - Task has multiple steps? Complete them in sequence
   - Don't assume - verify results first

5. COMPLETION:
   - Set is_complete=true ONLY when ALL steps are done
   - If task needs GUI (editing file content, visual interaction), set needs_handoff=true
   - Use full paths (~/Documents, ~/Downloads, etc.)

CURRENT STEP: {step}

⚠️  CRITICAL RULES:
- DO NOT repeat failed commands
- DO NOT repeat successful steps
- DO build on previous success
- DO try different approaches when stuck

Generate the next command:
"""

        try:
            structured_llm = self.llm_client.with_structured_output(ShellCommand)
            decision = await structured_llm.ainvoke(prompt)
            return decision
        except Exception as e:
            console.print(f"  [yellow]Warning: LLM error: {e}[/yellow]")
            return ShellCommand(
                command="echo 'error'",
                reasoning="LLM failed",
                is_complete=True,
            )

    def _execute_command(self, command: str) -> Dict[str, Any]:
        """
        Execute shell command safely.

        Args:
            command: Shell command to execute

        Returns:
            Result dictionary with output or error
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(__import__("pathlib").Path.home()),
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "output": result.stdout,
                    "command": command,
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr or "Command failed",
                    "command": command,
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timed out (30s)",
                "command": command,
            }
        except Exception as e:
            return {"success": False, "error": str(e), "command": command}
