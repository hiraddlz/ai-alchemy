"""Image -> ASCII art conversion."""

from __future__ import annotations

from PIL import Image, ImageEnhance

# Each charset is ordered from darkest (background) to lightest (foreground).
CHARSETS: dict[str, str] = {
    "Simple": " .:-=+*#%@",
    "Detailed": " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$",
    "Blocks": " ░▒▓█",
    "Binary": " 01",
}


def image_to_ascii(
    image: Image.Image,
    width: int = 100,
    charset: str = CHARSETS["Simple"],
    *,
    invert: bool = False,
    brightness: float = 1.0,
    contrast: float = 1.0,
) -> str:
    """Render ``image`` as a grid of characters ``width`` columns wide.

    ``invert`` flips the palette, which is what you want for dark backgrounds.
    """
    if width < 1:
        raise ValueError("width must be positive")
    if len(charset) < 2:
        raise ValueError("charset needs at least two characters")

    gray = image.convert("L")
    if brightness != 1.0:
        gray = ImageEnhance.Brightness(gray).enhance(brightness)
    if contrast != 1.0:
        gray = ImageEnhance.Contrast(gray).enhance(contrast)

    # Terminal glyphs are roughly twice as tall as they are wide.
    aspect = gray.height / gray.width
    height = max(1, round(width * aspect * 0.5))
    gray = gray.resize((width, height), Image.LANCZOS)

    palette = charset[::-1] if invert else charset
    scale = (len(palette) - 1) / 255
    pixels = list(gray.tobytes())  # one 0-255 value per pixel, row-major
    rows = []
    for row_start in range(0, width * height, width):
        row = pixels[row_start : row_start + width]
        rows.append("".join(palette[round(p * scale)] for p in row))
    return "\n".join(rows)
