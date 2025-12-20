"""Delegation tools for Browser-Use.

These tools allow the Browser-Use autonomous agent to temporarily delegate
OS-native dialog handling (file pickers, permission prompts) to the existing
CrewAI GUI specialist agent, then resume browser control.

This is intentionally generic: the Browser-Use agent provides the task context,
and the GUI agent uses its toolset to execute the dialog flow.
"""

from typing import Optional

from browser_use import ActionResult, Tools


def load_delegation_tools(gui_delegate=None) -> Optional[Tools]:
    """Load delegation tools if a GUI delegate is provided."""
    if gui_delegate is None:
        return None

    tools = Tools()

    @tools.action(
        description=(
            "Delegate OS-native dialog handling to GUI agent. "
            "Use for file pickers/permission prompts. "
            "Do NOT use for CAPTCHA/QR/2FA (use request_human_help)."
        )
    )
    def delegate_to_gui(task: str) -> ActionResult:
        """Delegate an OS dialog task to the GUI specialist and return control."""
        result = gui_delegate.run_os_dialog_task(task)

        if result.success:
            return ActionResult(
                extracted_content=(
                    "GUI delegation completed. Resume the browser task and verify the page state.\n\n"
                    f"GUI RESULT:\n{result.output}"
                ),
                long_term_memory=f"Delegated OS dialog task: {task}",
            )

        return ActionResult(
            extracted_content=(
                "GUI delegation did not complete successfully. "
                "Adapt your approach, retry with clearer instructions, or use request_human_help if truly human-only.\n\n"
                f"GUI RESULT:\n{result.output}"
            ),
            error="GUI delegation failed",
        )

    return tools
