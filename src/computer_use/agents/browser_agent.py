"""
Browser agent for web automation using Browser-Use.
Contains Browser-Use Agent creation and execution logic.
"""

from pathlib import Path
from typing import Optional
import tempfile
import glob
import logging

from ..schemas.actions import ActionResult
from ..schemas.browser_output import BrowserOutput, FileDetail
from ..prompts.browser_prompts import build_full_context
from ..tools.browser import load_browser_tools


class BrowserAgent:
    """
    Web automation specialist using Browser-Use library.
    Handles all web-based tasks with Browser-Use autonomous agent.
    """

    def __init__(self, llm_client):
        """
        Initialize browser agent with Browser-Use.

        Args:
            llm_client: LLM client for Browser-Use Agent
        """
        self.llm_client = llm_client
        self.browser_tools = load_browser_tools()  # Loads tools internally
        self.available = self._initialize_browser()

    def _initialize_browser(self) -> bool:
        """
        Initialize Browser-Use library.

        Returns:
            True if initialization successful
        """
        try:
            from browser_use import BrowserSession

            self.BrowserSession = BrowserSession
            return True
        except ImportError:
            print("Browser-Use not available. Install with: pip install browser-use")
            return False

    async def execute_task(
        self, task: str, url: Optional[str] = None, context: dict = None
    ) -> ActionResult:
        """
        Execute web automation task using Browser-Use Agent.

        Browser-Use handles everything: navigation, clicking, typing, data extraction.
        We pass the task and it figures out all the actions needed.

        Args:
            task: Natural language task description
            url: Optional starting URL (unused - Browser-Use navigates automatically)
            context: Optional context from previous agents (unused for now)

        Returns:
            ActionResult with browser output and file tracking
        """
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
            from browser_use import Agent, BrowserSession, BrowserProfile
            from browser_use.agent.views import AgentHistoryList

            logging.basicConfig(level=logging.DEBUG)
            browser_use_logger = logging.getLogger("browser_use")
            browser_use_logger.setLevel(logging.DEBUG)

            has_tools = self.browser_tools is not None
            tool_context = build_full_context(has_twilio=has_tools)
            full_task = tool_context + "\n\n" + task

            temp_dir = Path(tempfile.mkdtemp(prefix="browser_agent_"))

            print(f"[BrowserAgent] Creating new browser session for task: {task}")
            browser_session = BrowserSession(browser_profile=BrowserProfile())
            print(f"[BrowserAgent] Browser session created: {browser_session}")

            agent = Agent(
                task=full_task,
                llm=self.llm_client,
                browser_session=browser_session,
                tools=self.browser_tools,  # Pass Tools object directly or None
                max_failures=5,
            )

            print("[BrowserAgent] Running agent with max_steps=30")
            result: AgentHistoryList = await agent.run(max_steps=30)
            print(f"[BrowserAgent] Agent finished: {result.is_done()}")

            agent_called_done = result.is_done()
            task_completed_successfully = result.is_successful()
            final_output = result.final_result()

            downloaded_files = []
            file_details = []

            search_locations = [
                Path(tempfile.gettempdir()),
                Path("/tmp"),
                Path("/private/tmp"),
            ]

            seen_dirs = set()
            for temp_base in search_locations:
                if not temp_base.exists():
                    continue

                search_pattern = str(temp_base / "browser-use-downloads-*")
                found_dirs = glob.glob(search_pattern)

                for download_dir in found_dirs:
                    download_path = Path(download_dir).resolve()
                    if str(download_path) in seen_dirs:
                        continue
                    seen_dirs.add(str(download_path))

                    if download_path.exists():
                        for file_path in download_path.rglob("*"):
                            if file_path.is_file():
                                abs_path = str(file_path.absolute())
                                if abs_path not in downloaded_files:
                                    downloaded_files.append(abs_path)
                                    file_details.append(
                                        FileDetail(
                                            path=abs_path,
                                            name=file_path.name,
                                            size=file_path.stat().st_size,
                                        )
                                    )

            print("[BrowserAgent] Killing browser session")
            try:
                await browser_session.kill()
                print("[BrowserAgent] Browser session killed successfully")
            except Exception as kill_error:
                print(f"[BrowserAgent] Error killing browser session: {kill_error}")

            if result.history and len(result.history) > 0:
                last_result = result.history[-1].result
                if last_result and len(last_result) > 0:
                    attachments = last_result[-1].attachments
                    if attachments:
                        for attachment in attachments:
                            attachment_path = Path(attachment)
                            if attachment_path.exists():
                                downloaded_files.append(str(attachment_path.absolute()))
                                file_details.append(
                                    FileDetail(
                                        path=str(attachment_path.absolute()),
                                        name=attachment_path.name,
                                        size=attachment_path.stat().st_size,
                                    )
                                )

            browser_data_dir = temp_dir / "browseruse_agent_data"
            if browser_data_dir.exists():
                for file_path in browser_data_dir.rglob("*"):
                    if (
                        file_path.is_file()
                        and str(file_path.absolute()) not in downloaded_files
                    ):
                        downloaded_files.append(str(file_path.absolute()))
                        file_details.append(
                            FileDetail(
                                path=str(file_path.absolute()),
                                name=file_path.name,
                                size=file_path.stat().st_size,
                            )
                        )

            error_list = result.errors()
            has_errors = any(e for e in error_list if e)
            error_msgs = [str(e) for e in error_list if e]

            browser_output = BrowserOutput(
                text=final_output or "Task completed",
                files=downloaded_files,
                file_details=file_details,
                work_directory=str(temp_dir),
            )

            if agent_called_done:
                return ActionResult(
                    success=(
                        task_completed_successfully
                        if task_completed_successfully is not None
                        else False
                    ),
                    action_taken=f"Browser task: {task}",
                    method_used="browser",
                    confidence=1.0 if task_completed_successfully else 0.5,
                    data={
                        "result": str(result),
                        "output": browser_output.model_dump(),
                        "task_complete": True,
                    },
                )
            elif has_errors and error_msgs:
                return ActionResult(
                    success=False,
                    action_taken=f"Browser task failed: {task}",
                    method_used="browser",
                    confidence=0.0,
                    error="; ".join(error_msgs),
                    data={
                        "result": str(result),
                        "output": browser_output.model_dump(),
                    },
                )

            return ActionResult(
                success=True,
                action_taken=f"Browser task: {task}",
                method_used="browser",
                confidence=0.9,
                data={
                    "result": str(result),
                    "output": browser_output.model_dump(),
                },
            )

        except Exception as e:
            error_msg = str(e)
            print(f"[BrowserAgent] Exception during browser task: {error_msg}")

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
