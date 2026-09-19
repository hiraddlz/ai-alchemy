"""Streaming chatbot with switchable personas."""

from __future__ import annotations

import streamlit as st

from ai_alchemy.ui import page_header, require_client, stream_to_ui

PERSONAS = {
    "General assistant": "You are a helpful, concise assistant. Use Markdown when it aids clarity.",
    "Senior software engineer": (
        "You are a senior software engineer. Give precise, practical answers with code examples, "
        "mention trade-offs, and prefer standard-library solutions when reasonable."
    ),
    "Socratic tutor": (
        "You are a patient tutor. Guide the user to the answer with questions and hints rather "
        "than giving it away immediately, unless they explicitly ask for the solution."
    ),
    "Career coach": (
        "You are a career coach with experience in tech hiring. Be encouraging but candid, and "
        "give actionable advice."
    ),
}


def render() -> None:
    page_header("Chatbot", "💬", "Streaming conversation with a persona of your choice.")
    client = require_client()

    st.session_state.setdefault("chat_messages", [])

    top_left, top_right = st.columns([3, 1])
    with top_left:
        persona = st.selectbox("Persona", list(PERSONAS), label_visibility="collapsed")
    with top_right:
        if st.button("🗑️ Clear chat", use_container_width=True):
            st.session_state.chat_messages = []
            st.rerun()

    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask anything..."):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            messages = [
                {"role": "system", "content": PERSONAS[persona]},
                *st.session_state.chat_messages,
            ]
            reply = stream_to_ui(client.stream(messages))
        if reply:
            st.session_state.chat_messages.append({"role": "assistant", "content": reply})
        else:  # drop the user turn so a retry does not duplicate it
            st.session_state.chat_messages.pop()
