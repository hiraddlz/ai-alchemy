"""Turn one piece of content into platform-specific posts."""

from __future__ import annotations

import streamlit as st

from ai_alchemy.llm import strip_code_fences
from ai_alchemy.ui import example_button, page_header, require_client, stream_to_ui

PLATFORMS = {
    "LinkedIn": (
        "a LinkedIn post of 120-200 words: a strong first line as the hook, short paragraphs, "
        "one concrete insight or lesson, a closing question to invite comments, 3-5 relevant hashtags at the end"
    ),
    "X / Twitter thread": (
        "a thread of 4-7 tweets, each under 260 characters, numbered like 1/, 2/ ...; the first tweet "
        "must stand on its own as a hook and the last should summarise or call to action"
    ),
    "Instagram caption": (
        "an Instagram caption: an engaging opening line, 2-4 short lines of value, emojis used sparingly, "
        "a call to action, then a block of 8-12 hashtags"
    ),
    "Email newsletter": (
        "a newsletter section: a subject line, a preview line, then 150-250 words with a friendly intro, "
        "the key points as a short list, and a single clear link-style call to action"
    ),
    "Blog intro": "a 150-word blog post introduction that frames the problem, hints at the payoff and ends with a transition into the body",
}
TONES = ["Professional", "Casual", "Witty", "Inspirational", "Educational"]

PROMPT = """You are a social media strategist. Rewrite the user's content as {platform}, in a {tone} tone.
Use only the ideas and facts in the source - never invent statistics, names or claims.
Output the post text only, ready to paste, with no commentary or code fences."""

SAMPLE = """We just finished migrating our monolith to a set of services over eight months. Three lessons: start with the data model, not the network boundaries - most of our pain was shared tables. Second, invest in observability before the first service ships; tracing saved us weeks. Third, do it incrementally - the strangler pattern let us ship value every sprint instead of a big-bang cutover. Deploy frequency went from twice a month to 30+ times a week, and p95 latency dropped 40%."""


def render() -> None:
    page_header("Content Repurposer", "♻️", "One idea, every platform - without inventing anything.")
    client = require_client()

    text = st.text_area(
        "Source content",
        height=220,
        key="rp_text",
        placeholder="A blog post, notes, a transcript...",
    )
    example_button("Load a sample", "rp_text", SAMPLE)

    c1, c2 = st.columns([3, 1])
    platforms = c1.multiselect(
        "Platforms", list(PLATFORMS), default=["LinkedIn", "X / Twitter thread"]
    )
    tone = c2.selectbox("Tone", TONES)

    if not st.button(
        "🚀 Generate", type="primary", use_container_width=True, disabled=not platforms
    ):
        return
    if not text.strip():
        st.warning("Paste some source content first.")
        return

    tabs = st.tabs(platforms)
    for tab, platform in zip(tabs, platforms, strict=True):
        with tab:
            prompt = PROMPT.format(platform=PLATFORMS[platform], tone=tone.lower())
            placeholder = st.empty()
            with placeholder.container():
                output = stream_to_ui(client.complete_stream(prompt, text, temperature=0.7))
            if output:
                output = strip_code_fences(output)
                # Swap the streamed Markdown for a copyable block once complete.
                placeholder.code(output, language=None, wrap_lines=True)
                st.caption(f"{len(output)} characters")
