"""
UI Theme configuration: colors, icons, and styles.
"""

from typing import Dict

THEME: Dict[str, str] = {
    "agent_active": "#00ff88",
    "agent_idle": "#666666",
    "agent_box": "#30363d",
    "tool_pending": "#ffaa00",
    "tool_success": "#00ff00",
    "tool_error": "#ff4444",
    "thinking": "#aaaaff",
    "input": "#ffcc00",
    "output": "#00ccff",
    "text": "#e6edf3",
    "muted": "#7d8590",
    "error": "#f85149",
    "warning": "#d29922",
    "border": "#30363d",
    "header": "#ffffff",
    "panel_bg": "#0d1117",
    "phase_thinking": "#aaaaff",
    "phase_executing": "#ffaa00",
    "phase_waiting": "#7d8590",
    "timing_fast": "#00ff88",
    "timing_normal": "#7d8590",
    "timing_slow": "#d29922",
    "hud_border": "#3d444d",
    "hud_dim": "#8b949e",
    "hud_muted": "#484f58",
    "hud_text": "#c9d1d9",
    "hud_active": "#58a6ff",
    "hud_success": "#3fb950",
    "hud_error": "#f85149",
    "hud_pending": "#d29922",
}

ICONS: Dict[str, str] = {
    "pending": "⟳",
    "success": "✓",
    "error": "✗",
    "warning": "⚠",
    "agent_active": "●",
    "agent_idle": "○",
    "delegated": "→",
    "thinking": "┊",
    "input": "→",
    "output": "←",
    "tool": "🔧",
    "browser": "🌐",
    "terminal": "💻",
    "code": "📝",
    "bullet": "•",
    "arrow": "❯",
    "separator": "│",
    "phase_thinking": "◐",
    "phase_executing": "⚙",
    "phase_waiting": "◯",
}

HEADSET_BLINK_FRAMES = ["◐", "◓", "◑", "◒"]
PROGRESS_BAR_CHARS = [" ", "▏", "▎", "▍", "▌", "▋", "▊", "▉", "█"]
