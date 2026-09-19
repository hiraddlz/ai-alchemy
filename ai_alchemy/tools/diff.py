"""Word-level diff rendering (original vs. corrected text)."""

from __future__ import annotations

from redlines import Redlines


def diff_markdown(original: str, corrected: str) -> str:
    """Return Markdown/HTML that highlights deletions and insertions."""
    if original.strip() == corrected.strip():
        return "_No changes._"
    return Redlines(original, corrected).output_markdown
