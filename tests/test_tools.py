"""Unit tests for the framework-free helpers in ``ai_alchemy.tools``."""

from __future__ import annotations

import pytest
from PIL import Image

from ai_alchemy.tools.ascii_art import CHARSETS, image_to_ascii
from ai_alchemy.tools.diff import diff_markdown
from ai_alchemy.tools.documents import extract_text, truncate_words
from ai_alchemy.tools.youtube import extract_video_id

# ------------------------------------------------------------------ ascii


def test_ascii_dimensions_follow_aspect_ratio():
    art = image_to_ascii(Image.new("L", (200, 100), 128), width=40)
    rows = art.split("\n")
    assert len(rows) == 10  # 40 * 0.5 aspect * 0.5 glyph correction
    assert all(len(row) == 40 for row in rows)


def test_ascii_black_and_white_map_to_palette_ends():
    charset = CHARSETS["Simple"]
    black = image_to_ascii(Image.new("L", (10, 10), 0), width=5, charset=charset)
    white = image_to_ascii(Image.new("L", (10, 10), 255), width=5, charset=charset)
    assert set(black.replace("\n", "")) == {charset[0]}
    assert set(white.replace("\n", "")) == {charset[-1]}


def test_ascii_invert_swaps_ends():
    charset = CHARSETS["Simple"]
    black = image_to_ascii(Image.new("L", (10, 10), 0), width=5, charset=charset, invert=True)
    assert set(black.replace("\n", "")) == {charset[-1]}


def test_ascii_rejects_bad_input():
    with pytest.raises(ValueError):
        image_to_ascii(Image.new("L", (10, 10)), width=0)
    with pytest.raises(ValueError):
        image_to_ascii(Image.new("L", (10, 10)), charset="x")


# ---------------------------------------------------------------- youtube


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.youtube.com/watch?feature=share&v=dQw4w9WgXcQ&t=42",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ?si=abc",
        "https://www.youtube.com/shorts/dQw4w9WgXcQ",
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
        "https://www.youtube.com/live/dQw4w9WgXcQ",
        "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
        "youtube.com/watch?v=dQw4w9WgXcQ",
        "dQw4w9WgXcQ",
    ],
)
def test_extract_video_id_accepts_common_forms(url):
    assert extract_video_id(url) == "dQw4w9WgXcQ"


@pytest.mark.parametrize(
    "url",
    [
        "https://vimeo.com/12345",
        "https://www.youtube.com/",
        "not a url",
        "https://www.youtube.com/watch?v=short",
    ],
)
def test_extract_video_id_rejects_invalid(url):
    assert extract_video_id(url) is None


# ------------------------------------------------------------- documents


def test_extract_text_plain_and_markdown():
    assert extract_text("a.txt", b"hello") == "hello"
    assert extract_text("a.md", "# héllo".encode()) == "# héllo"


def test_extract_text_docx(tmp_path):
    docx = pytest.importorskip("docx", reason="python-docx not installed")
    path = tmp_path / "r.docx"
    doc = docx.Document()
    doc.add_paragraph("Résumé line one")
    doc.save(path)
    assert "Résumé line one" in extract_text("r.docx", path.read_bytes())


def test_extract_text_pdf_blank_page():
    import io

    pdfium = pytest.importorskip("pypdfium2")
    pdf = pdfium.PdfDocument.new()
    pdf.new_page(200, 100)
    buffer = io.BytesIO()
    pdf.save(buffer)
    # A blank page has no text; the point is that parsing bytes works end-to-end.
    assert extract_text("blank.pdf", buffer.getvalue()) == ""


def test_extract_text_unknown_extension():
    with pytest.raises(ValueError):
        extract_text("archive.zip", b"")


def test_truncate_words():
    assert truncate_words("a b c", 5) == ("a b c", False)
    assert truncate_words("a b c d e f", 3) == ("a b c", True)


# ------------------------------------------------------------------ diff


def test_diff_marks_insertions_and_deletions():
    html = diff_markdown("I has a cat", "I have a cat")
    assert "has" in html and "have" in html
    assert "line-through" in html


def test_diff_identical_text():
    assert diff_markdown("same", "same ") == "_No changes._"
