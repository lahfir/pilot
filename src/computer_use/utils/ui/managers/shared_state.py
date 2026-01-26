"""
Shared dashboard state for UI managers.

This module provides a single mutable object that stores all runtime UI state
required by the dashboard. Managers operate on this state object to avoid
duplicated state tracking and to keep each module small and focused.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set

from ..state import TaskState


@dataclass
class DashboardSharedState:
    """Runtime state shared across dashboard managers."""

    task: Optional[TaskState] = None
    is_running: bool = False

    printed_agents: Set[str] = field(default_factory=set)
    printed_tools: Set[str] = field(default_factory=set)
    started_tools: Set[str] = field(default_factory=set)
    nested_tools: Set[str] = field(default_factory=set)

    last_thought_hash: Optional[int] = None
    header_printed: bool = False
    current_agent_name: Optional[str] = None

    pending_thought: Optional[str] = None
    pending_thought_agent_id: Optional[str] = None

    tool_history: list[Dict[str, Any]] = field(default_factory=list)
