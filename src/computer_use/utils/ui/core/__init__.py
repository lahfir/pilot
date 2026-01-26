"""
Core terminal rendering infrastructure.

This package centralizes terminal output and enables flicker-free updates via
Rich Live. Higher-level UI modules interact with this package rather than
printing directly.
"""

from .render_manager import RenderManager

__all__ = ["RenderManager"]
