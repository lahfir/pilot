"""
Intelligent coordinator agent that decides which agent to use next.
"""

from typing import TYPE_CHECKING
from ..schemas.workflow import CoordinatorDecision, WorkflowContext

if TYPE_CHECKING:
    from ..utils.platform_detector import PlatformCapabilities


class CoordinatorAgent:
    """
    Simple coordinator that decides which agent goes next.
    """

    def __init__(self, llm_client, capabilities: "PlatformCapabilities"):
        """
        Initialize coordinator agent.

        Args:
            llm_client: LLM client for intelligent analysis and planning
            capabilities: PlatformCapabilities object (typed, not a dict!)
        """
        self.llm_client = llm_client
        self.capabilities = capabilities

    async def decide_next_action(
        self, original_task: str, context: WorkflowContext
    ) -> CoordinatorDecision:
        """
        Decide next agent and subtask based on current context.

        Args:
            original_task: Original user task
            context: Current workflow context with previous results

        Returns:
            CoordinatorDecision with agent, subtask, and completion status
        """
        context_summary = self._format_context(context)

        prompt = f"""
You are coordinating multiple agents to complete a task.

ORIGINAL TASK: "{original_task}"

CONTEXT SO FAR:
{context_summary}

AVAILABLE AGENTS:
- browser: Web browsing, research, downloading files from websites
- gui: Desktop applications (Calculator, Notes, Preview, etc), visual UIs
- system: File operations, shell commands, organizing files

DECIDE NEXT ACTION:
1. Is the task complete? If yes, set is_complete=True
2. If not, which agent should go next?
3. What specific subtask should they do?
4. Why this agent/subtask?

Think about:
- What has already been done?
- What still needs to be done?
- Which agent is best for the next step?
"""

        structured_llm = self.llm_client.with_structured_output(CoordinatorDecision)
        decision = await structured_llm.ainvoke(prompt)

        return decision

    def _format_context(self, context: WorkflowContext) -> str:
        """
        Format workflow context for LLM prompt.

        Args:
            context: Current workflow context

        Returns:
            Formatted context string
        """
        if not context.agent_results:
            return "No previous actions yet - this is the first step."

        parts = []
        for i, result in enumerate(context.agent_results, 1):
            status = "✓" if result.success else "✗"
            parts.append(
                f"Step {i}: {status} {result.agent} - {result.subtask}\n"
                f"  Result: {result.data if result.success else result.error}"
            )

        return "\n".join(parts)
