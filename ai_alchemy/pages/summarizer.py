"""Summarise pasted text or an uploaded document."""

from __future__ import annotations

import streamlit as st

from ai_alchemy.tools.documents import SUPPORTED_EXTENSIONS, extract_text, truncate_words
from ai_alchemy.ui import (
    example_button,
    page_header,
    require_client,
    show_error,
    stream_to_ui,
    word_count,
)

MAX_WORDS = 60_000

FORMATS = {
    "Bullet points": "a list of 5-10 bullet points, each a self-contained takeaway",
    "Paragraph": "one or two well-structured paragraphs",
    "TL;DR": "a single sentence TL;DR followed by three supporting bullets",
    "Executive brief": "sections titled Context, Key findings, Implications and Recommended actions",
}
LENGTHS = {"Short": "about 80 words", "Medium": "about 180 words", "Long": "about 350 words"}

PROMPT = """You are a precise summariser. Produce {fmt}, {length}, in {language}.
Preserve concrete facts, numbers and names; drop filler; never add information that is not in the source.
Output Markdown only."""

SAMPLE = """The James Webb Space Telescope (JWST) is the largest optical telescope in space. Launched on 25 December 2021 on an Ariane 5 rocket from Kourou, French Guiana, it reached its destination at the second Lagrange point (L2), about 1.5 million kilometres from Earth, in January 2022. Its 6.5-metre primary mirror is made of 18 hexagonal gold-coated beryllium segments and gives it roughly six times the light-collecting area of the Hubble Space Telescope. Unlike Hubble, which observes mainly in visible and ultraviolet light, JWST is optimised for infrared, letting it see through dust clouds and observe the most distant, highly red-shifted galaxies formed a few hundred million years after the Big Bang. A five-layer sunshield the size of a tennis court keeps the instruments below 50 kelvin. The project, led by NASA with ESA and the Canadian Space Agency, cost about US$10 billion and was more than a decade late, but its first images in July 2022 were widely hailed as transformative for astronomy."""


def render() -> None:
    page_header(
        "Summarizer", "🧠", "Condense articles, reports or whole documents into the shape you need."
    )
    client = require_client()

    text_tab, file_tab = st.tabs(["✍️ Paste text", "📄 Upload a file"])
    with text_tab:
        text = st.text_area(
            "Text",
            height=260,
            key="sum_text",
            label_visibility="collapsed",
            placeholder="Paste anything...",
        )
        example_button("Load a sample", "sum_text", SAMPLE)
    with file_tab:
        uploaded = st.file_uploader("Document", type=list(SUPPORTED_EXTENSIONS))
        if uploaded is not None:
            try:
                text = extract_text(uploaded.name, uploaded.getvalue())
                st.success(f"Loaded **{uploaded.name}** · {word_count(text):,} words")
            except Exception as exc:  # noqa: BLE001
                show_error(exc)

    c1, c2, c3 = st.columns(3)
    fmt = c1.selectbox("Format", list(FORMATS))
    length = c2.select_slider("Length", list(LENGTHS), value="Medium")
    language = c3.selectbox(
        "Output language",
        ["Same as source", "English", "Spanish", "French", "German", "Persian", "Chinese"],
    )

    if not st.button("🚀 Summarise", type="primary", use_container_width=True):
        return
    if not text or not text.strip():
        st.warning("Paste some text or upload a file first.")
        return

    text, clipped = truncate_words(text, MAX_WORDS)
    if clipped:
        st.warning(f"Input was clipped to the first {MAX_WORDS:,} words.")

    lang = "the same language as the source text" if language == "Same as source" else language
    prompt = PROMPT.format(fmt=FORMATS[fmt], length=LENGTHS[length], language=lang)
    st.markdown("#### Summary")
    summary = stream_to_ui(client.complete_stream(prompt, text))
    if summary:
        st.caption(f"{word_count(text):,} words → {word_count(summary):,} words")
        st.download_button(
            "⬇️ Download summary", summary, file_name="summary.md", mime="text/markdown"
        )
