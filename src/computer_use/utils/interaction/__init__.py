"""
User interaction utilities for confirmations and OCR targeting.
"""

from .command_confirmation import CommandConfirmation
from .ocr_targeting import (
    compute_spatial_score,
    determine_text_relation,
    filter_candidates_by_spatial_context,
    is_word_boundary_match,
    score_ocr_candidate,
)

__all__ = [
    "CommandConfirmation",
    "compute_spatial_score",
    "determine_text_relation",
    "filter_candidates_by_spatial_context",
    "is_word_boundary_match",
    "score_ocr_candidate",
]
