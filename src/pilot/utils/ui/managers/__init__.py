"""
Dashboard manager modules.

These modules split the dashboard responsibilities into focused components to
keep each file under the project size limit and to make the rendering backend
swappable without changing callers.
"""

from .agent_display import AgentDisplay
from .log_batcher import LogBatcher
from .shared_state import DashboardSharedState
from .status_manager import StatusManager
from .task_manager import TaskManager
from .tool_display import ToolDisplay

__all__ = [
    "AgentDisplay",
    "DashboardSharedState",
    "LogBatcher",
    "StatusManager",
    "TaskManager",
    "ToolDisplay",
]
