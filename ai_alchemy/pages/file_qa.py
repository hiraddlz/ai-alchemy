"""Chat with the contents of an uploaded document."""

from __future__ import annotations

import streamlit as st

from ai_alchemy.tools.documents import SUPPORTED_EXTENSIONS, extract_text, truncate_words
from ai_alchemy.ui import page_header, require_client, show_error, stream_to_ui, word_count

MAX_WORDS = 60_000  # ~80k tokens; keeps us inside common context windows

SYSTEM_PROMPT = """You are a meticulous analyst answering questions about a document.
Answer using only the document below. Quote short passages when useful and say clearly
when the document does not contain the answer. Use Markdown.

<document name="{name}">
{text}
</document>"""


def render() -> None:
    page_header("File Q&A", "📁", "Ask questions grounded in a PDF, Word or text document.")
    client = require_client()

    uploaded = st.file_uploader("Upload a document", type=list(SUPPORTED_EXTENSIONS))
    if uploaded is None:
        st.session_state.pop("fileqa", None)
        st.info(
            "Upload a file to start. Text is extracted locally and sent to the model with each question."
        )
        return

    state = st.session_state.get("fileqa")
    if state is None or state["file_id"] != uploaded.file_id:
        try:
            with st.spinner("Extracting text..."):
                text = extract_text(uploaded.name, uploaded.getvalue())
        except Exception as exc:  # noqa: BLE001
            show_error(exc)
            return
        if not text.strip():
            st.warning("No text could be extracted. Scanned PDFs need OCR first.")
            return
        text, clipped = truncate_words(text, MAX_WORDS)
        state = {
            "file_id": uploaded.file_id,
            "name": uploaded.name,
            "text": text,
            "clipped": clipped,
            "messages": [],
        }
        st.session_state.fileqa = state

    info, action = st.columns([4, 1])
    info.caption(
        f"📄 **{state['name']}** · {word_count(state['text']):,} words"
        + (" · clipped to fit the context window" if state["clipped"] else "")
    )
    if action.button("🗑️ Clear chat", use_container_width=True):
        state["messages"] = []
        st.rerun()

    with st.expander("Preview extracted text"):
        st.text(state["text"][:3000] + ("..." if len(state["text"]) > 3000 else ""))

    for message in state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    suggestions = [
        "Summarise this document in 5 bullets",
        "What are the key numbers or dates?",
        "List any action items",
    ]
    if not state["messages"]:
        question = st.pills("Try one", suggestions, label_visibility="collapsed")
    else:
        question = None
    question = st.chat_input("Ask about the document...") or question

    if question:
        state["messages"].append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            system = SYSTEM_PROMPT.format(name=state["name"], text=state["text"])
            reply = stream_to_ui(
                client.stream([{"role": "system", "content": system}, *state["messages"]])
            )
        if reply:
            state["messages"].append({"role": "assistant", "content": reply})
        else:
            state["messages"].pop()
