"""
Crew execution utilities for hierarchical crew.

Handles crew creation and execution logic.
"""

import asyncio
import time
from typing import Dict

from crewai import Agent, Crew, Process, Task

from ...schemas import TaskExecutionResult
from ...utils.logging import debug_log, extract_result_token_usage
from ...utils.ui import dashboard, print_failure, print_success


class CrewExecutor:
    """
    Utility class for executing CrewAI hierarchical crews.
    """

    @staticmethod
    def create_crew(
        agents_dict: Dict[str, Agent],
        manager_task: Task,
    ) -> Crew:
        """
        Create a CrewAI hierarchical crew instance.

        Args:
            agents_dict: Dictionary of agent keys to Agent instances
            manager_task: Manager task for delegation

        Returns:
            Configured Crew instance
        """
        specialist_agents = [
            agents_dict["browser_agent"],
            agents_dict["gui_agent"],
            agents_dict["system_agent"],
            agents_dict["coding_agent"],
        ]

        return Crew(
            agents=specialist_agents,
            tasks=[manager_task],
            process=Process.hierarchical,
            manager_agent=agents_dict["manager"],
            verbose=dashboard.is_verbose,
        )

    @staticmethod
    async def execute_crew(
        crew: Crew,
        task: str,
        cancellation_check_fn: callable,
    ) -> TaskExecutionResult:
        """
        Execute a CrewAI crew and handle results/errors.

        Args:
            crew: CrewAI Crew instance
            task: Task description
            cancellation_check_fn: Function to check if cancelled

        Returns:
            TaskExecutionResult with execution outcome
        """
        loop = asyncio.get_event_loop()
        try:
            t0 = time.time()
            debug_log(
                "H_CREW_KICKOFF",
                "crew_executor.py:execute_crew:before_kickoff",
                "Calling CrewAI kickoff in executor",
                {"executor_loop_running": bool(loop.is_running())},
            )
            result = await loop.run_in_executor(None, crew.kickoff)
            debug_log(
                "H_CREW_KICKOFF",
                "crew_executor.py:execute_crew:after_kickoff",
                "CrewAI kickoff returned",
                {
                    "elapsed_ms": int((time.time() - t0) * 1000),
                    "result_type": type(result).__name__,
                },
            )

            prompt, completion = extract_result_token_usage(result)
            if prompt > 0 or completion > 0:
                dashboard.update_token_usage(prompt, completion)

            result_str = str(result)
            print_success("Execution completed")
            return TaskExecutionResult(
                task=task, result=result_str, overall_success=True
            )
        except Exception as exc:
            import traceback

            tb_str = traceback.format_exc()
            print(f"\n[CREW ERROR] {type(exc).__name__}: {exc}")
            print(f"[TRACEBACK]\n{tb_str[:500]}")
            debug_log(
                "H_CREW_KICKOFF",
                "crew_executor.py:execute_crew:exception",
                "CrewAI kickoff raised",
                {
                    "exc_type": type(exc).__name__,
                    "exc_str": str(exc)[:500],
                    "traceback": tb_str[:1000],
                },
            )
            if cancellation_check_fn():
                print_failure("Task cancelled by user")
                return TaskExecutionResult(
                    task=task,
                    result=None,
                    overall_success=False,
                    error="Task cancelled by user",
                )
            print_failure(f"Execution failed: {exc}")
            return TaskExecutionResult(task=task, overall_success=False, error=str(exc))
