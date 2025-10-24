"""
Browser agent for web automation using Browser-Use.
"""

from ..schemas.actions import ActionResult


class BrowserAgent:
    """
    Web automation specialist using Browser-Use library.
    Handles all web-based tasks with high accuracy.
    """

    def __init__(self, tool_registry):
        """
        Initialize browser agent.

        Args:
            tool_registry: PlatformToolRegistry instance
        """
        self.tool_registry = tool_registry
        self.browser_tool = tool_registry.get_tool("browser")

    async def execute_task(
        self, task: str, url: str = None, context: dict = None
    ) -> ActionResult:
        """
        Execute web automation task.

        Args:
            task: Natural language task description
            url: Optional starting URL
            context: Context from previous agents

        Returns:
            ActionResult with status and data
        """
        # Add smart handoff guidelines (generic, principle-based)
        handoff_guidelines = """
═══════════════════════════════════════════════════════════
🎯 BROWSER AGENT: WEB AUTOMATION SPECIALIST
═══════════════════════════════════════════════════════════

CORE COMPETENCIES:
- Navigate websites, search, extract information
- Download files to disk (images, PDFs, documents)
- Fill forms, interact with web UI
- Extract data from pages

OTHER AGENTS HANDLE:
- Desktop applications (GUI agent)
- File system operations (System agent)
- Installing/running programs

═══════════════════════════════════════════════════════════
CRITICAL: UNDERSTANDING "DOWNLOAD"
═══════════════════════════════════════════════════════════

DOWNLOAD = SAVE TO DISK (file must exist in file system)

❌ WRONG - These are NOT downloads:
- Opening image in new browser tab
- Viewing file in browser
- Displaying content on screen
- Right-clicking but not saving

✅ CORRECT - These ARE downloads:
- Right-click image → "Save Image As" → file saved to disk
- Click "Download" button → file saved to Downloads folder
- Right-click link → "Save Link As" → file saved to disk

DECISION FRAMEWORK FOR DOWNLOADS:

1. LOCATE: Find the target (image, file, document)
2. TRIGGER SAVE: 
   - Right-click on image/link → look for "Save" option
   - Click explicit "Download" button if available
   - Use browser's save functionality
3. VERIFY: File saved to disk (not just opened in tab)
4. DONE: Call done() ONLY after file is saved to disk

VERIFICATION CHECKLIST:
Before calling done() for download task, ask yourself:
→ Did I right-click and select "Save"?
→ Did I click a "Download" button?
→ Is the file saved to disk (not just viewed)?

If any answer is NO → You haven't completed the download!

═══════════════════════════════════════════════════════════
"""

        enhanced_task = handoff_guidelines + "\n\n"

        if context and context.get("previous_results"):
            prev_results = context.get("previous_results", [])
            if prev_results:
                context_info = "CONTEXT - Previous work done:\n"
                for res in prev_results:
                    agent_type = res.get("method_used", "unknown")
                    action = res.get("action_taken", "")
                    success = "✅" if res.get("success") else "❌"
                    context_info += f"{success} {agent_type}: {action}\n"
                enhanced_task += context_info + "\n\n"

        enhanced_task += f"YOUR TASK: {task}"

        try:
            result = await self.browser_tool.execute_task(enhanced_task, url)
            return result
        except Exception as e:
            return ActionResult(
                success=False,
                action_taken=task,
                method_used="browser",
                confidence=0.0,
                error=str(e),
            )
