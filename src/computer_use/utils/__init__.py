"""
Utility modules organized by domain.

Submodules:
- platform: Platform detection, capabilities, permissions
- validation: Coordinate, safety, and reasoning validation
- logging: Logging configuration, status, and metrics
- interaction: User confirmation and OCR targeting
- ui: Dashboard, prompts, and rendering
"""

from .platform import PlatformCapabilities, PlatformHelper, detect_platform
from .validation import CoordinateValidator, SafetyChecker

__all__ = [
    "PlatformCapabilities",
    "detect_platform",
    "PlatformHelper",
    "SafetyChecker",
    "CoordinateValidator",
]
