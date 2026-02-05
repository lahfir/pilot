"""
Tier 2: Computer vision and OCR tools for element detection.
"""

from .ocr_tool import OCRTool
from .ocr_protocol import OCREngine
from .ocr_factory import create_ocr_engine, detect_gpu_availability

__all__ = [
    "OCRTool",
    "OCREngine",
    "create_ocr_engine",
    "detect_gpu_availability",
]
