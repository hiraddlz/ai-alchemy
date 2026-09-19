"""Text extraction from uploaded documents."""

from __future__ import annotations

import io
from typing import BinaryIO

SUPPORTED_EXTENSIONS = ("pdf", "docx", "txt", "md")


def extract_text(name: str, data: bytes | BinaryIO) -> str:
    """Return the plain text of a PDF, DOCX, TXT or Markdown file."""
    raw = data if isinstance(data, bytes) else data.read()
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""

    if ext == "pdf":
        return _pdf_text(raw)
    if ext == "docx":
        import docx2txt

        return docx2txt.process(io.BytesIO(raw)) or ""
    if ext in ("txt", "md", ""):
        return raw.decode("utf-8", errors="replace")
    raise ValueError(f"Unsupported file type: .{ext}")


def _pdf_text(raw: bytes) -> str:
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(raw)
    try:
        pages = [page.get_textpage().get_text_range() for page in pdf]
    finally:
        pdf.close()
    return "\n\n".join(p.strip() for p in pages if p and p.strip())


def truncate_words(text: str, max_words: int) -> tuple[str, bool]:
    """Clip ``text`` to ``max_words``; the flag reports whether clipping happened."""
    words = text.split()
    if len(words) <= max_words:
        return text, False
    return " ".join(words[:max_words]), True
