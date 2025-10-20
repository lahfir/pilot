"""
Cross-platform screenshot capture tool.
"""

import base64
import io
from typing import Optional, Tuple
from PIL import Image
import pyautogui


class ScreenshotTool:
    """
    Cross-platform screenshot capture with region support.
    Handles Retina/HiDPI display scaling automatically.
    """

    def __init__(self):
        """
        Initialize and detect display scaling.
        """
        self.scaling_factor = self._detect_scaling()

    def _detect_scaling(self) -> float:
        """
        Detect display scaling factor (Retina = 2.0, normal = 1.0).
        """
        import platform

        screen_size = pyautogui.size()
        test_screenshot = pyautogui.screenshot()

        # If screenshot is larger than screen, we have scaling
        if test_screenshot.width > screen_size.width:
            scaling = test_screenshot.width / screen_size.width
            return scaling
        return 1.0

    def capture(
        self, region: Optional[Tuple[int, int, int, int]] = None
    ) -> Image.Image:
        """
        Capture screenshot of entire screen or specific region.

        Args:
            region: Optional region as (x, y, width, height) in SCREEN coordinates

        Returns:
            PIL Image object at full resolution
        """
        if region:
            # Scale region to screenshot coordinates
            x, y, w, h = region
            scaled_region = (
                int(x * self.scaling_factor),
                int(y * self.scaling_factor),
                int(w * self.scaling_factor),
                int(h * self.scaling_factor),
            )
            screenshot = pyautogui.screenshot(region=scaled_region)
        else:
            screenshot = pyautogui.screenshot()

        return screenshot

    def capture_as_base64(
        self, region: Optional[Tuple[int, int, int, int]] = None, format: str = "PNG"
    ) -> str:
        """
        Capture screenshot and return as base64 string.

        Args:
            region: Optional region as (x, y, width, height)
            format: Image format (PNG, JPEG, etc.)

        Returns:
            Base64 encoded screenshot
        """
        screenshot = self.capture(region=region)

        buffer = io.BytesIO()
        screenshot.save(buffer, format=format)
        buffer.seek(0)

        encoded = base64.b64encode(buffer.read()).decode("utf-8")
        return encoded

    def save(
        self, filepath: str, region: Optional[Tuple[int, int, int, int]] = None
    ) -> str:
        """
        Capture and save screenshot to file.

        Args:
            filepath: Path to save screenshot
            region: Optional region as (x, y, width, height)

        Returns:
            Path where screenshot was saved
        """
        screenshot = self.capture(region=region)
        screenshot.save(filepath)
        return filepath

    def get_pixel_color(self, x: int, y: int) -> Tuple[int, int, int]:
        """
        Get RGB color of pixel at specified coordinates.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            RGB tuple (r, g, b)
        """
        screenshot = self.capture()
        return screenshot.getpixel((x, y))
