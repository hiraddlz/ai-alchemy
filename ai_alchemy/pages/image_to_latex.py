"""Equation image -> LaTeX using a vision model."""

from __future__ import annotations

import streamlit as st

from ai_alchemy.llm import strip_code_fences
from ai_alchemy.ui import page_header, require_client, show_error

PROMPT = """Transcribe every mathematical expression in this image into LaTeX.
Rules:
- Output only LaTeX math, with no surrounding $ or \\[ \\] delimiters, no prose, no code fences.
- Put each separate equation on its own line, using \\\\ between lines and align if needed.
- Prefer standard amsmath commands (\\frac, \\sum, \\int, \\begin{aligned} ...).
- If part of the image is unreadable, write \\text{[unreadable]} in its place."""


def render() -> None:
    page_header(
        "Image to LaTeX",
        "🧮",
        "Snap an equation - printed or handwritten - and get compilable LaTeX.",
    )
    client = require_client()
    st.caption("Requires a vision-capable model (gpt-4o-mini, gemini-2.0-flash, llava, ...).")

    uploaded = st.file_uploader("Image of an equation", type=["png", "jpg", "jpeg", "webp"])
    if uploaded is None:
        return

    image_col, result_col = st.columns([1, 1])
    with image_col:
        st.image(uploaded, use_container_width=True)

    with result_col:
        if not st.button("🚀 Convert", type="primary", use_container_width=True):
            return
        try:
            with st.spinner("Reading the equation..."):
                latex = client.describe_image(
                    PROMPT, uploaded.getvalue(), uploaded.type or "image/png", temperature=0
                )
        except Exception as exc:  # noqa: BLE001
            show_error(exc)
            return
        latex = strip_code_fences(latex).strip("$ \n")

        st.markdown("##### Rendered")
        with st.container(border=True):
            try:
                st.latex(latex)
            except Exception:  # noqa: BLE001 - KaTeX rendering issues surface client-side anyway
                st.warning("Could not render; the LaTeX below may need a small fix.")

        st.markdown("##### LaTeX")
        st.code(latex, language="latex", wrap_lines=True)
        st.download_button("⬇️ Download .tex", latex, file_name="equation.tex", mime="text/plain")
