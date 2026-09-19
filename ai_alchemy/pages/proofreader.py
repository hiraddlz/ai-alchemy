"""Grammar and spelling correction with a word-level diff."""

from __future__ import annotations

import streamlit as st

from ai_alchemy.llm import strip_code_fences
from ai_alchemy.tools.diff import diff_markdown
from ai_alchemy.ui import example_button, page_header, require_client, show_error, stream_to_ui

MODES = {
    "Fix errors only": "Correct spelling, grammar and punctuation. Keep the wording, tone and structure otherwise unchanged.",
    "Fix + tighten": "Correct all errors and make the text more concise and readable, without changing its meaning or tone.",
    "Fix + formal": "Correct all errors and rewrite in a polished, formal register suitable for business or academic use.",
}

CORRECT_PROMPT = """You are an expert copy editor. {mode}
Preserve paragraph breaks and any Markdown. Output only the corrected text - no preamble, no quotes, no code fences."""

EXPLAIN_PROMPT = """You are an English teacher. Compare the original and corrected text and list the
changes as a Markdown bullet list: quote the change and explain the rule in one short sentence.
Group trivial repeated fixes. Maximum 10 bullets."""

SAMPLE = """Their are many reason why people chooses to learn a second language. Some does it for there career, other's because they wants to travel. Irregardless of the motivation, studies has shown that bilingual people tends to have better memory, and are more creative then monolinguals."""


def render() -> None:
    page_header("Proofreader", "🔍", "Fix mistakes, see exactly what changed, and learn why.")
    client = require_client()

    text = st.text_area(
        "Text to proofread", height=220, key="pf_text", placeholder="Paste your text..."
    )
    example_button("Load a sample", "pf_text", SAMPLE)

    controls = st.columns([2, 1])
    mode = controls[0].radio("Mode", list(MODES), horizontal=True)
    explain = controls[1].toggle("Explain the changes", value=True)

    if not st.button("✨ Proofread", type="primary", use_container_width=True):
        return
    if not text.strip():
        st.warning("Enter some text first.")
        return

    st.markdown("#### Corrected text")
    corrected = stream_to_ui(
        client.complete_stream(CORRECT_PROMPT.format(mode=MODES[mode]), text, temperature=0)
    )
    if not corrected:
        return
    corrected = strip_code_fences(corrected)

    st.markdown("#### Changes")
    st.markdown(diff_markdown(text, corrected), unsafe_allow_html=True)
    st.download_button(
        "⬇️ Download corrected text", corrected, file_name="corrected.txt", mime="text/plain"
    )

    if explain and corrected.strip() != text.strip():
        st.markdown("#### Why")
        try:
            stream_to_ui(
                client.complete_stream(
                    EXPLAIN_PROMPT,
                    f"<original>\n{text}\n</original>\n<corrected>\n{corrected}\n</corrected>",
                    temperature=0,
                )
            )
        except Exception as exc:  # noqa: BLE001
            show_error(exc)
