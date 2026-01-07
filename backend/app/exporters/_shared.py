"""Helpers shared by the text-based exporters."""
from __future__ import annotations

from ..models import FileResult


def format_timestamp(seconds: float) -> str:
    """Return HH:MM:SS from a float number of seconds."""
    seconds = max(0, int(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def language_label(result: FileResult) -> str:
    langs = sorted({s.language for s in result.segments if s.language})
    if not langs:
        return result.detected_language or "unknown"
    return ", ".join(langs)
