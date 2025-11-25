"""
Live status updates for terminal UI - Claude-code style experience.
Real-time feedback that updates in-place and clears when done.
"""

import threading
from contextlib import contextmanager
from typing import Optional
from enum import Enum
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text


console = Console()


class ActionType(Enum):
    """Types of actions for visual distinction."""

    CLICK = "click"
    TYPE = "type"
    SCROLL = "scroll"
    OPEN = "open"
    READ = "read"
    SEARCH = "search"
    NAVIGATE = "navigate"
    WAIT = "wait"
    EXECUTE = "execute"
    ANALYZE = "analyze"


ACTION_ICONS = {
    ActionType.CLICK: "🖱️ ",
    ActionType.TYPE: "⌨️ ",
    ActionType.SCROLL: "📜",
    ActionType.OPEN: "📂",
    ActionType.READ: "👁️ ",
    ActionType.SEARCH: "🔍",
    ActionType.NAVIGATE: "🌐",
    ActionType.WAIT: "⏳",
    ActionType.EXECUTE: "⚡",
    ActionType.ANALYZE: "🧠",
}

ACTION_VERBS = {
    ActionType.CLICK: "Clicking",
    ActionType.TYPE: "Typing",
    ActionType.SCROLL: "Scrolling",
    ActionType.OPEN: "Opening",
    ActionType.READ: "Reading",
    ActionType.SEARCH: "Searching",
    ActionType.NAVIGATE: "Navigating to",
    ActionType.WAIT: "Waiting for",
    ActionType.EXECUTE: "Executing",
    ActionType.ANALYZE: "Analyzing",
}


class LiveStatus:
    """
    Singleton for managing live status updates.
    Provides Claude-code style terminal experience.
    """

    _instance: Optional["LiveStatus"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._live: Optional[Live] = None
        self._current_action: Optional[str] = None
        self._spinner_active = False
        self._action_stack: list = []
        self._console = Console()

    def _create_status_display(
        self, action_type: ActionType, target: str, detail: Optional[str] = None
    ) -> Text:
        """
        Create a styled status display.

        Args:
            action_type: Type of action being performed
            target: Target element/location
            detail: Optional detail text

        Returns:
            Styled Text object
        """
        icon = ACTION_ICONS.get(action_type, "⚙️ ")
        verb = ACTION_VERBS.get(action_type, "Processing")

        text = Text()
        text.append(f"  {icon} ", style="bold")
        text.append(f"{verb} ", style="cyan bold")
        text.append(f"'{target}'", style="yellow")

        if detail:
            text.append(f" • {detail}", style="dim")

        return text

    @contextmanager
    def action(
        self, action_type: ActionType, target: str, detail: Optional[str] = None
    ):
        """
        Context manager for action with live spinner that clears on completion.

        Args:
            action_type: Type of action
            target: Target of the action
            detail: Optional detail

        Example:
            with live_status.action(ActionType.CLICK, "Submit button"):
                # perform click
                pass
            # Spinner automatically clears
        """
        status_text = self._create_status_display(action_type, target, detail)
        spinner = Spinner("dots", text=status_text, style="cyan")

        self._action_stack.append((action_type, target))

        try:
            with Live(
                spinner, console=self._console, refresh_per_second=10, transient=True
            ):
                yield
        finally:
            self._action_stack.pop() if self._action_stack else None

    def show_success(self, message: str, target: Optional[str] = None):
        """
        Show success message (stays visible).

        Args:
            message: Success message
            target: Optional target that succeeded
        """
        text = Text()
        text.append("  ✓ ", style="green bold")
        text.append(message, style="green")
        if target:
            text.append(f" '{target}'", style="yellow")
        self._console.print(text)

    def show_failure(self, message: str, error: Optional[str] = None):
        """
        Show failure message (stays visible).

        Args:
            message: Failure message
            error: Optional error detail
        """
        text = Text()
        text.append("  ✗ ", style="red bold")
        text.append(message, style="red")
        if error:
            text.append(f" ({error})", style="dim red")
        self._console.print(text)

    def show_info(self, message: str):
        """
        Show info message.

        Args:
            message: Info message
        """
        text = Text()
        text.append("  ℹ ", style="blue bold")
        text.append(message, style="blue")
        self._console.print(text)

    def show_warning(self, message: str):
        """
        Show warning message.

        Args:
            message: Warning message
        """
        text = Text()
        text.append("  ⚠ ", style="yellow bold")
        text.append(message, style="yellow")
        self._console.print(text)

    @contextmanager
    def task_group(self, title: str):
        """
        Context manager for a group of related tasks.

        Args:
            title: Group title
        """
        self._console.print()
        header = Text()
        header.append("┌─ ", style="dim")
        header.append(title, style="bold cyan")
        self._console.print(header)

        try:
            yield
        finally:
            footer = Text()
            footer.append("└─", style="dim")
            self._console.print(footer)
            self._console.print()


class ActionProgress:
    """
    Track and display multi-step action progress.
    Shows a clean progress indicator for complex operations.
    """

    def __init__(self, total_steps: int, title: str = "Progress"):
        """
        Initialize progress tracker.

        Args:
            total_steps: Total number of steps
            title: Progress title
        """
        self.total = total_steps
        self.current = 0
        self.title = title
        self._console = Console()
        self._live: Optional[Live] = None

    def _render(self) -> Text:
        """Render progress bar."""
        filled = int((self.current / self.total) * 20)
        empty = 20 - filled

        text = Text()
        text.append(f"  {self.title} ", style="cyan")
        text.append("[", style="dim")
        text.append("█" * filled, style="green")
        text.append("░" * empty, style="dim")
        text.append("]", style="dim")
        text.append(f" {self.current}/{self.total}", style="dim")

        return text

    def __enter__(self):
        self._live = Live(self._render(), console=self._console, transient=True)
        self._live.__enter__()
        return self

    def __exit__(self, *args):
        if self._live:
            self._live.__exit__(*args)

    def advance(self, step_name: Optional[str] = None):
        """
        Advance progress by one step.

        Args:
            step_name: Optional name of completed step
        """
        self.current += 1
        if self._live:
            self._live.update(self._render())


def format_element_info(
    element_type: str, label: str, location: Optional[tuple] = None
) -> str:
    """
    Format element information for display.

    Args:
        element_type: Type of element (button, text, etc.)
        label: Element label
        location: Optional (x, y) coordinates

    Returns:
        Formatted string
    """
    parts = [f"{element_type}"]
    if label:
        parts.append(f'"{label}"')
    if location:
        parts.append(f"at ({location[0]}, {location[1]})")
    return " ".join(parts)


live_status = LiveStatus()
