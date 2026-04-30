"""
ElectIQ — Input Validation and Sanitisation Utilities
All user input must pass through these functions before processing.
"""
import re
import bleach
from typing import Optional


# ── Compiled Patterns ──────────────────────────────────────────────────────────
EPIC_PATTERN = re.compile(r"^[A-Z]{3}[0-9]{7}$")
CONSTITUENCY_PATTERN = re.compile(r"^[A-Za-z\s]{2,50}$")
LANG_PATTERN = re.compile(r"^[a-z]{2,5}$")


def sanitise(text: str, max_len: int = 2000) -> str:
    """
    Sanitise and truncate user-supplied text input.
    Strips HTML tags, normalises whitespace, and enforces length limit.
    """
    if not text or not isinstance(text, str):
        return ""
    return bleach.clean(text.strip())[:max_len]


def is_valid_epic(epic: str) -> bool:
    """Return True if epic matches the ECI EPIC format (3 letters + 7 digits)."""
    return bool(EPIC_PATTERN.match(epic))


def is_valid_constituency(name: str) -> bool:
    """Return True if constituency name contains only safe alpha characters."""
    return bool(CONSTITUENCY_PATTERN.match(name))


def is_valid_language_code(code: str) -> bool:
    """Return True if language code is a valid ISO 639-1 code."""
    SUPPORTED = {"hi", "ta", "te", "bn", "mr", "gu", "kn", "ml", "pa", "ur"}
    return code in SUPPORTED and bool(LANG_PATTERN.match(code))


def validate_candidate_ids(ids: list) -> Optional[str]:
    """
    Validate a list of candidate IDs.
    Returns an error message string if invalid, else None.
    """
    if not isinstance(ids, list):
        return "ids must be a list"
    if len(ids) > 10:
        return "Too many IDs requested"
    if not all(isinstance(i, int) and 1 <= i <= 1000 for i in ids):
        return "Invalid candidate ID format"
    return None
