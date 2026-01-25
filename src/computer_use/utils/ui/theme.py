"""
UI Theme configuration: colors, icons, and styles.
"""

from typing import Dict

THEME: Dict[str, str] = {
    # Agent States
    "agent_active": "#00ff88",  # Bright green
    "agent_idle": "#666666",  # Gray
    "agent_box": "#30363d",  # Dark gray border
    # Tool States
    "tool_pending": "#ffaa00",  # Orange
    "tool_success": "#00ff00",  # Green
    "tool_error": "#ff4444",  # Red
    # Text Types
    "thinking": "#aaaaff",  # Light blue/purple
    "input": "#ffcc00",  # Gold/Yellow
    "output": "#00ccff",  # Cyan
    "text": "#e6edf3",  # Main text
    "muted": "#7d8590",  # Muted text
    "error": "#f85149",  # Error red
    "warning": "#d29922",  # Warning yellow
    # UI Elements
    "border": "#30363d",
    "header": "#ffffff",
    "panel_bg": "#0d1117",
    # Phase Colors
    "phase_thinking": "#aaaaff",  # Purple for LLM reasoning
    "phase_executing": "#ffaa00",  # Orange for tool execution
    "phase_waiting": "#7d8590",  # Muted for waiting
    # Timing Colors
    "timing_fast": "#00ff88",  # Green for <1s
    "timing_normal": "#7d8590",  # Gray for 1-5s
    "timing_slow": "#d29922",  # Yellow for >5s
}

ICONS: Dict[str, str] = {
    # Status Icons
    "pending": "⟳",  # Will be animated
    "success": "✓",
    "error": "✗",
    "warning": "⚠",
    # Agent Icons
    "agent_active": "●",
    "agent_idle": "○",
    "delegated": "→",
    # Action Icons
    "thinking": "┊",
    "input": "→",
    "output": "←",
    "tool": "🔧",
    "browser": "🌐",
    "terminal": "💻",
    "code": "📝",
    # Decorative
    "bullet": "•",
    "arrow": "❯",
    "separator": "│",
    # Phase Icons
    "phase_thinking": "◐",
    "phase_executing": "⚙",
    "phase_waiting": "◯",
}

SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
PROGRESS_BAR_CHARS = [" ", "▏", "▎", "▍", "▌", "▋", "▊", "▉", "█"]
