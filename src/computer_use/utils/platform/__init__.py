"""
Platform detection, capabilities, and permission utilities.
"""

from .platform_detector import PlatformCapabilities, detect_platform
from .platform_helper import PlatformHelper
from .permissions import (
    PermissionChecker,
    PermissionStatus,
    check_and_request_permissions,
    get_permission_summary,
)

__all__ = [
    "PlatformCapabilities",
    "detect_platform",
    "PlatformHelper",
    "PermissionChecker",
    "PermissionStatus",
    "check_and_request_permissions",
    "get_permission_summary",
]
