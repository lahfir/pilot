"""
Browser agent for web automation using Browser-Use.
Contains Browser-Use Agent creation and execution logic.
"""

from pathlib import Path
from typing import Optional
import tempfile
import glob
import platform
import os

from ..schemas.actions import ActionResult
from ..schemas.browser_output import BrowserOutput, FileDetail
from ..prompts.browser_prompts import build_full_context
from ..tools.browser import load_browser_tools


def get_default_chrome_paths() -> dict:
    """
    Get platform-specific default Chrome paths.

    Returns:
        Dictionary with executable_path and user_data_dir for the current platform.
    """
    system = platform.system()

    if system == "Darwin":
        return {
            "executable_path": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "user_data_dir": os.path.expanduser(
                "~/Library/Application Support/Google/Chrome"
            ),
        }
    elif system == "Windows":
        return {
            "executable_path": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "user_data_dir": os.path.expandvars(
                r"%LOCALAPPDATA%\Google\Chrome\User Data"
            ),
        }
    elif system == "Linux":
        return {
            "executable_path": "/usr/bin/google-chrome",
            "user_data_dir": os.path.expanduser("~/.config/google-chrome"),
        }
    else:
        return {"executable_path": None, "user_data_dir": None}


class BrowserAgent:
    """Web automation specialist using Browser-Use library."""

    def __init__(
        self,
        llm_client,
        use_user_profile: bool = False,
        user_data_dir: Optional[str] = None,
        profile_directory: str = "Default",
        executable_path: Optional[str] = None,
        headless: bool = False,
        gui_delegate=None,
    ):
        """Initialize browser agent with Browser-Use.

        Args:
            llm_client: LLM client for Browser-Use Agent
            use_user_profile: If True, use existing Chrome user profile for authentication
            user_data_dir: Path to Chrome user data directory (auto-detected if not provided)
            profile_directory: Chrome profile name (Default, Profile 1, etc.)
            executable_path: Path to Chrome executable (auto-detected if not provided)
            headless: Run browser in headless mode (no visible window)
            gui_delegate: Optional GUI delegation bridge for OS-native dialogs
        """
        self.llm_client = llm_client
        self.use_user_profile = use_user_profile
        self.profile_directory = profile_directory
        self.headless = headless
        self.gui_delegate = gui_delegate

        self._configure_profile_paths(user_data_dir, executable_path)

        self.browser_tools, self.has_twilio, self.has_image_gen = load_browser_tools(
            gui_delegate=gui_delegate
        )
        self.available = self._initialize_browser()

    def _configure_profile_paths(
        self, user_data_dir: Optional[str], executable_path: Optional[str]
    ) -> None:
        """Configure Chrome profile paths, using defaults if not provided."""
        defaults = get_default_chrome_paths()

        self.user_data_dir = user_data_dir or defaults.get("user_data_dir")
        self.executable_path = executable_path or defaults.get("executable_path")

    def _create_browser_session(self):
        """Create BrowserSession with user profile settings if enabled."""
        from browser_use import BrowserSession

        if self.use_user_profile and self.user_data_dir:
            return BrowserSession(
                is_local=True,
                executable_path=self.executable_path,
                headless=self.headless,
                args=["--disable-extensions"],
            )

        return BrowserSession(is_local=True, headless=self.headless)

    def _initialize_browser(self) -> bool:
        """Initialize Browser-Use library."""
        try:
            from browser_use import BrowserSession

            self.BrowserSession = BrowserSession
            return True
        except ImportError:
            return False

    async def execute_task(
        self, task: str, url: Optional[str] = None, context: dict = None
    ) -> ActionResult:
        """Execute web automation task using Browser-Use Agent."""
        if not self.available:
            return ActionResult(
                success=False,
                action_taken="Browser initialization failed",
                method_used="browser",
                confidence=0.0,
                error="Browser-Use not initialized. Install with: pip install browser-use",
            )

        if not self.llm_client:
            return ActionResult(
                success=False,
                action_taken="No LLM client provided",
                method_used="browser",
                confidence=0.0,
                error="No LLM client provided for Browser-Use Agent",
            )

        try:
            import logging

            from browser_use import Agent
            from browser_use.agent.views import AgentHistoryList

            from ..utils.ui import dashboard, ActionType, VerbosityLevel

            def step_callback(browser_state, agent_output, step_num):
                """Callback for browser-use agent step updates."""
                dashboard.set_agent("Browser Agent")

                if hasattr(agent_output, "current_state"):
                    state = agent_output.current_state
                    if (
                        hasattr(state, "evaluation_previous_goal")
                        and state.evaluation_previous_goal
                    ):
                        dashboard.add_log_entry(
                            ActionType.ANALYZE,
                            f"Eval: {state.evaluation_previous_goal[:100]}",
                            status="complete",
                        )
                    if hasattr(state, "memory") and state.memory:
                        dashboard.set_thinking(state.memory[:150])
                    if hasattr(state, "next_goal") and state.next_goal:
                        dashboard.set_action("Browser", target=state.next_goal[:80])

                if hasattr(agent_output, "actions") and agent_output.actions:
                    for action in agent_output.actions:
                        action_name = action.__class__.__name__
                        action_dict = (
                            action.model_dump() if hasattr(action, "model_dump") else {}
                        )
                        action_params = ", ".join(
                            f"{k}={str(v)[:30]}"
                            for k, v in list(action_dict.items())[:3]
                        )
                        dashboard.log_tool_start(f"Browser: {action_name}", action_dict)
                        dashboard.add_log_entry(
                            ActionType.EXECUTE,
                            (
                                f"{action_name}({action_params})"
                                if action_params
                                else action_name
                            ),
                        )

            def done_callback(history):
                """Callback when browser-use agent completes."""
                if history.is_successful():
                    dashboard.add_log_entry(
                        ActionType.COMPLETE,
                        "Browser task completed successfully",
                        status="complete",
                    )
                else:
                    errors = history.errors()
                    if errors:
                        dashboard.add_log_entry(
                            ActionType.ERROR,
                            f"Browser task failed: {errors[0] if errors else 'Unknown error'}",
                            status="error",
                        )

            browser_loggers = [
                "browser_use",
                "browser_use.agent",
                "browser_use.browser",
                "browser_use.dom",
                "BrowserSession",
                "httpx",
                "httpcore",
            ]

            class NullHandler(logging.Handler):
                def emit(self, record):
                    pass

            for logger_name in browser_loggers:
                logger = logging.getLogger(logger_name)
                logger.handlers = [NullHandler()]
                logger.setLevel(logging.CRITICAL)
                logger.propagate = False

            if dashboard.verbosity == VerbosityLevel.VERBOSE:
                console_handler = logging.StreamHandler()
                console_handler.setLevel(logging.INFO)
                for logger_name in browser_loggers[:2]:
                    logger = logging.getLogger(logger_name)
                    logger.handlers = [console_handler]
                    logger.setLevel(logging.INFO)

            tool_context = build_full_context(
                has_twilio=self.has_twilio,
                has_image_gen=self.has_image_gen,
                has_gui_delegate=self.gui_delegate is not None,
            )
            full_task = tool_context + "\n\n" + task

            temp_dir = Path(tempfile.mkdtemp(prefix="browser_agent_"))

            browser_session = self._create_browser_session()
            dashboard.set_browser_session(active=True, profile=None)

            available_files = []
            if self.has_image_gen:
                from computer_use.tools.browser.image_tools import (
                    get_generated_image_paths,
                )

                available_files.extend(get_generated_image_paths())

            agent = Agent(
                task=full_task,
                llm=self.llm_client,
                browser_session=browser_session,
                tools=self.browser_tools,
                max_failures=10,
                register_new_step_callback=step_callback,
                register_done_callback=done_callback,
                available_file_paths=available_files if available_files else None,
            )

            result: AgentHistoryList = await agent.run(max_steps=200)

            try:
                await browser_session.kill()
            except Exception:
                pass
            finally:
                dashboard.set_browser_session(active=False)

            downloaded_files = []
            file_details = []

            download_dirs = glob.glob(
                str(Path(tempfile.gettempdir()) / "browser-use-downloads-*")
            )
            for download_dir in download_dirs:
                for file_path in Path(download_dir).rglob("*"):
                    if file_path.is_file():
                        downloaded_files.append(str(file_path.absolute()))
                        file_details.append(
                            FileDetail(
                                path=str(file_path.absolute()),
                                name=file_path.name,
                                size=file_path.stat().st_size,
                            )
                        )

            browser_output = BrowserOutput(
                text=result.final_result() or "Task completed",
                files=downloaded_files,
                file_details=file_details,
                work_directory=str(temp_dir),
            )

            is_successful = result.is_successful()
            has_errors = bool(result.errors())

            if result.is_done():
                success = is_successful if is_successful is not None else not has_errors
                error_msg = (
                    "; ".join(str(e) for e in result.errors() if e)
                    if has_errors
                    else None
                )

                return ActionResult(
                    success=success,
                    action_taken=f"Browser task: {task}",
                    method_used="browser",
                    confidence=1.0 if success else 0.0,
                    error=error_msg,
                    data=browser_output.model_dump(),
                )

            return ActionResult(
                success=not has_errors,
                action_taken=f"Browser task: {task}",
                method_used="browser",
                confidence=0.5,
                error=(
                    "Agent reached max steps without completing" if has_errors else None
                ),
                data=browser_output.model_dump(),
            )

        except Exception as e:
            error_msg = str(e)
            dashboard.add_log_entry(
                ActionType.ERROR, f"Browser exception: {error_msg[:80]}", status="error"
            )

            if "Event loop is closed" in error_msg:
                error_msg = (
                    "Browser session event loop error (browser-use library issue with async cleanup). "
                    f"Original error: {error_msg}"
                )

            return ActionResult(
                success=False,
                action_taken=f"Browser task exception: {task}",
                method_used="browser",
                confidence=0.0,
                error=error_msg,
            )
