"""
OCR tool for text detection with precise coordinates.
"""

from typing import List, Optional, Tuple
from PIL import Image
import numpy as np


class OCRTool:
    """
    Text detection with precise bounding box coordinates.
    Uses EasyOCR for accurate text recognition.
    """

    def __init__(self):
        """
        Initialize OCR tool with EasyOCR reader.
        """
        self.reader = None
        self._initialize_reader()

    def _initialize_reader(self):
        """
        Lazy initialization of EasyOCR reader.
        """
        try:
            import easyocr

            self.reader = easyocr.Reader(["en"], gpu=False)
        except ImportError:
            print("EasyOCR not available. Install with: pip install easyocr")
            self.reader = None

    def find_text(
        self,
        screenshot: Image.Image,
        target_text: str,
        region: Optional[Tuple[int, int, int, int]] = None,
        fuzzy: bool = True,
    ) -> List[dict]:
        """
        Find text in screenshot and return exact bounding boxes.

        Args:
            screenshot: PIL Image to search
            target_text: Text to find
            region: Optional region to search (x, y, width, height)
            fuzzy: Whether to allow partial matches

        Returns:
            List of dictionaries with text and bounding boxes
        """
        if self.reader is None:
            return []

        if region:
            x, y, w, h = region
            screenshot = screenshot.crop((x, y, x + w, y + h))
            offset_x, offset_y = x, y
        else:
            offset_x, offset_y = 0, 0

        img_array = np.array(screenshot)

        try:
            results = self.reader.readtext(img_array)
        except Exception as e:
            print(f"OCR error: {e}")
            return []

        matches = []
        target_lower = target_text.lower()

        for bbox, text, confidence in results:
            text_lower = text.lower()

            if fuzzy:
                is_match = target_lower in text_lower or text_lower in target_lower
            else:
                is_match = text_lower == target_lower

            if is_match and confidence > 0.5:
                top_left = bbox[0]
                bottom_right = bbox[2]

                x = int(top_left[0]) + offset_x
                y = int(top_left[1]) + offset_y
                width = int(bottom_right[0] - top_left[0])
                height = int(bottom_right[1] - top_left[1])

                center_x = x + width // 2
                center_y = y + height // 2

                matches.append(
                    {
                        "text": text,
                        "bounds": (x, y, width, height),
                        "center": (center_x, center_y),
                        "confidence": confidence,
                        "detection_method": "ocr",
                    }
                )

        return matches

    def extract_all_text(self, screenshot: Image.Image) -> List[dict]:
        """
        Extract all text from screenshot with coordinates.

        Args:
            screenshot: PIL Image to analyze

        Returns:
            List of all detected text with coordinates
        """
        if self.reader is None:
            return []

        img_array = np.array(screenshot)

        try:
            results = self.reader.readtext(img_array)
        except Exception as e:
            print(f"OCR error: {e}")
            return []

        extracted = []

        for bbox, text, confidence in results:
            if confidence > 0.3:
                top_left = bbox[0]
                bottom_right = bbox[2]

                x = int(top_left[0])
                y = int(top_left[1])
                width = int(bottom_right[0] - top_left[0])
                height = int(bottom_right[1] - top_left[1])

                center_x = x + width // 2
                center_y = y + height // 2

                extracted.append(
                    {
                        "text": text,
                        "bounds": (x, y, width, height),
                        "center": (center_x, center_y),
                        "confidence": confidence,
                    }
                )

        return extracted

