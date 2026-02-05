"""
OCR tool for text detection with precise coordinates.
Includes LRU caching for performance optimization.
"""

import hashlib
from typing import List, Optional, Tuple
from PIL import Image

from .ocr_factory import create_ocr_engine, get_all_available_ocr_engines
from .ocr_protocol import OCREngine
from ...schemas.ocr_result import OCRResult


def _compute_image_hash(image: Image.Image) -> str:
    """
    Compute a fast hash of an image for cache keying.
    Uses a sample of pixels for speed while maintaining uniqueness.
    """
    small = image.resize((32, 32), Image.Resampling.NEAREST)
    data = small.tobytes()
    return hashlib.md5(data).hexdigest()


class OCRTool:
    """
    Text detection with precise bounding box coordinates.
    Uses platform-optimized OCR engines with automatic fallback.
    Includes LRU caching based on image hash for repeated OCR calls.
    """

    CACHE_SIZE = 32

    def __init__(self, use_gpu: Optional[bool] = None):
        """
        Initialize OCR tool with optimal engine for platform.

        Args:
            use_gpu: Whether to use GPU. If None, auto-detect.
        """
        self.engine: Optional[OCREngine] = None
        self.fallback_engines: List[OCREngine] = []
        self._initialize_engine(use_gpu)
        self._ocr_cache: dict = {}
        self._cache_order: list = []

    def _initialize_engine(self, use_gpu: Optional[bool]) -> None:
        """
        Initialize platform-optimized OCR engine and fallbacks.

        Args:
            use_gpu: Whether to use GPU
        """
        self.engine = create_ocr_engine(use_gpu=use_gpu)
        self.fallback_engines = get_all_available_ocr_engines(use_gpu=use_gpu)

    def find_text(
        self,
        screenshot: Image.Image,
        target_text: str,
        region: Optional[Tuple[int, int, int, int]] = None,
        fuzzy: bool = True,
    ) -> List[OCRResult]:
        """
        Find text in screenshot and return exact bounding boxes.
        Automatically tries fallback engines if primary fails.

        Args:
            screenshot: PIL Image to search
            target_text: Text to find
            region: Optional region to search (x, y, width, height)
            fuzzy: Whether to allow partial matches

        Returns:
            List of OCRResult objects with text and bounding boxes
        """
        if not self.fallback_engines:
            return []

        for engine in self.fallback_engines:
            try:
                results = engine.recognize_text(screenshot, region=region)

                if not results or len(results) == 0:
                    continue

                matches = []
                target_lower = target_text.lower()

                for result in results:
                    text = result.text
                    text_lower = text.lower()
                    confidence = result.confidence

                    if fuzzy:
                        if len(text_lower) < 3:
                            is_match = text_lower == target_lower
                        else:
                            is_match = (
                                target_lower in text_lower or text_lower in target_lower
                            )
                    else:
                        is_match = text_lower == target_lower

                    if is_match and confidence > 0.5:
                        matches.append(
                            OCRResult(
                                text=text,
                                bounds=result.bounds,
                                center=result.center,
                                confidence=confidence,
                                detection_method="ocr",
                            )
                        )

                if matches:
                    return matches

            except Exception:
                continue

        return []

    def _cache_get(self, key: str) -> Optional[List[OCRResult]]:
        """Retrieve from LRU cache."""
        return self._ocr_cache.get(key)

    def _cache_put(self, key: str, value: List[OCRResult]) -> None:
        """Store in LRU cache with size limit."""
        if key in self._ocr_cache:
            self._cache_order.remove(key)
        elif len(self._ocr_cache) >= self.CACHE_SIZE:
            oldest = self._cache_order.pop(0)
            del self._ocr_cache[oldest]

        self._ocr_cache[key] = value
        self._cache_order.append(key)

    def _perform_ocr(
        self, screenshot: Image.Image, region: Optional[Tuple[int, int, int, int]]
    ) -> List[OCRResult]:
        """Perform OCR with engine fallback."""
        if not self.fallback_engines:
            return []

        for engine in self.fallback_engines:
            try:
                results = engine.recognize_text(screenshot, region=region)
                if results and len(results) > 0:
                    return results
            except Exception:
                continue
        return []

    def extract_all_text(
        self, screenshot: Image.Image, use_cache: bool = True
    ) -> List[OCRResult]:
        """
        Extract all text from screenshot with coordinates.
        Uses LRU cache based on image hash for performance.

        Args:
            screenshot: PIL Image to analyze
            use_cache: Whether to use cached results if available

        Returns:
            List of all detected OCRResult objects with coordinates
        """
        if use_cache:
            img_hash = _compute_image_hash(screenshot)
            cache_key = f"all:{img_hash}"
            cached = self._cache_get(cache_key)
            if cached is not None:
                return cached

        results = self._perform_ocr(screenshot, None)
        extracted = [r for r in results if r.confidence > 0.3]

        if use_cache and extracted:
            self._cache_put(cache_key, extracted)

        return extracted

    def clear_cache(self) -> None:
        """Clear the OCR result cache."""
        self._ocr_cache.clear()
        self._cache_order.clear()
