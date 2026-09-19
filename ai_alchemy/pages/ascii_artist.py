"""Image -> ASCII art (runs entirely locally, no model needed)."""

from __future__ import annotations

import html

import streamlit as st
from PIL import Image

from ai_alchemy.tools.ascii_art import CHARSETS, image_to_ascii
from ai_alchemy.ui import page_header


def render() -> None:
    page_header(
        "ASCII Artist", "🎨", "Turn any picture into text art. Runs locally - no API key needed."
    )

    uploaded = st.file_uploader("Image", type=["png", "jpg", "jpeg", "webp", "gif", "bmp"])
    if uploaded is None:
        st.info("Upload a photo or logo. High-contrast images with a plain background work best.")
        return

    image = Image.open(uploaded)

    with st.sidebar:
        st.markdown("#### 🎨 ASCII settings")
        width = st.slider("Width (characters)", 40, 240, 120, 10)
        charset_name = st.selectbox("Character set", [*CHARSETS, "Custom"])
        charset = (
            st.text_input("Custom characters (dark → light)", " .oO@")
            if charset_name == "Custom"
            else CHARSETS[charset_name]
        )
        invert = st.toggle("Invert (for dark backgrounds)", value=True)
        brightness = st.slider("Brightness", 0.3, 2.0, 1.0, 0.05)
        contrast = st.slider("Contrast", 0.3, 2.5, 1.2, 0.05)

    if len(charset) < 2:
        st.warning("The character set needs at least two characters.")
        return

    art = image_to_ascii(
        image, width, charset, invert=invert, brightness=brightness, contrast=contrast
    )

    preview_col, art_col = st.columns([1, 2])
    with preview_col:
        st.image(image, caption=f"{image.width} × {image.height}px", use_container_width=True)
        st.download_button(
            "⬇️ Download .txt",
            art,
            file_name="ascii_art.txt",
            mime="text/plain",
            use_container_width=True,
        )
        st.caption(f"{width} × {art.count(chr(10)) + 1} characters")
    with art_col:
        st.html(f'<div class="ascii-art"><pre>{html.escape(art)}</pre></div>')
        with st.expander("Copy as text"):
            st.code(art, language=None)
