"""Translation with tone control and right-to-left rendering."""

from __future__ import annotations

import html

import streamlit as st

from ai_alchemy.llm import strip_code_fences
from ai_alchemy.ui import example_button, page_header, require_client, stream_to_ui

LANGUAGES = [
    "English", "Persian", "Arabic", "Spanish", "French", "German", "Italian", "Portuguese",
    "Turkish", "Russian", "Chinese (Simplified)", "Japanese", "Korean", "Hindi", "Urdu",
    "Hebrew", "Dutch", "Swedish", "Polish", "Indonesian", "Vietnamese",
]  # fmt: skip
RTL_LANGUAGES = {"Persian", "Arabic", "Urdu", "Hebrew"}
REGISTERS = {
    "Natural": "natural and idiomatic, as a native speaker would write it",
    "Formal": "formal and polite, suitable for official or business correspondence",
    "Casual": "casual and friendly, as in a message to a friend",
    "Literal": "as literal as possible while remaining grammatical, to aid language learners",
}

PROMPT = """You are a professional translator. Translate the user's text from {source} into {target}.
The translation should be {register}. Preserve formatting, line breaks, names, numbers and any Markdown.
Output only the translation - no explanations, no quotes, no code fences."""

SAMPLE = "The best time to plant a tree was twenty years ago. The second best time is now."


def render() -> None:
    page_header("Translator", "🌐", "Context-aware translation between 20+ languages.")
    client = require_client()

    c1, c2, c3 = st.columns([2, 2, 2])
    source = c1.selectbox("From", ["Auto-detect", *LANGUAGES])
    target = c2.selectbox("To", LANGUAGES, index=1)
    register = c3.selectbox("Style", list(REGISTERS))

    text = st.text_area("Text", height=200, key="tr_text", placeholder="Type or paste text...")
    example_button("Load a sample", "tr_text", SAMPLE)

    if not st.button("🚀 Translate", type="primary", use_container_width=True):
        return
    if not text.strip():
        st.warning("Enter some text first.")
        return

    prompt = PROMPT.format(
        source="the detected source language" if source == "Auto-detect" else source,
        target=target,
        register=REGISTERS[register],
    )
    st.markdown(f"#### {target}")
    if target in RTL_LANGUAGES:
        # Stream into a placeholder, then re-render with RTL direction.
        placeholder = st.empty()
        with placeholder.container():
            translation = stream_to_ui(client.complete_stream(prompt, text, temperature=0.2))
        if translation:
            translation = strip_code_fences(translation)
            placeholder.html(
                f'<div class="rtl">{html.escape(translation).replace(chr(10), "<br>")}</div>'
            )
    else:
        translation = stream_to_ui(client.complete_stream(prompt, text, temperature=0.2))
        translation = strip_code_fences(translation) if translation else None

    if translation:
        st.download_button(
            "⬇️ Download",
            translation,
            file_name=f"translation_{target.lower()}.txt",
            mime="text/plain",
        )
