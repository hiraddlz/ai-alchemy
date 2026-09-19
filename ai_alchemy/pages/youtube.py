"""Summarise a YouTube video from its transcript and chat about it."""

from __future__ import annotations

import streamlit as st

from ai_alchemy.tools.documents import truncate_words
from ai_alchemy.tools.youtube import extract_video_id, fetch_transcript
from ai_alchemy.ui import page_header, require_client, stream_to_ui, word_count

MAX_WORDS = 60_000

SUMMARY_PROMPT = """You are an expert at distilling talks and videos.
Write a summary of the transcript with this structure (Markdown):
**TL;DR** - two sentences.
**Key points** - 5 to 8 bullets, each a concrete takeaway.
**Notable quotes** - up to 3 short verbatim quotes, if any stand out.
Do not invent anything that is not in the transcript."""

CHAT_PROMPT = """You are answering questions about a YouTube video using only its transcript.
If the transcript does not cover something, say so.

<transcript>
{transcript}
</transcript>"""


def render() -> None:
    page_header(
        "YouTube Summarizer", "🎬", "Paste a link, get a structured summary, then ask follow-ups."
    )
    client = require_client()

    with st.form("yt_form", border=False):
        url_col, btn_col = st.columns([5, 1], vertical_alignment="bottom")
        url = url_col.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")
        submitted = btn_col.form_submit_button("Load", use_container_width=True, type="primary")

    if submitted:
        video_id = extract_video_id(url)
        if not video_id:
            st.error(
                "That does not look like a YouTube link. Supported: watch, youtu.be, shorts, embed, live."
            )
            return
        try:
            with st.spinner("Fetching transcript..."):
                transcript = fetch_transcript(video_id)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Could not fetch a transcript: {exc}")
            st.caption("Videos without captions (or with captions disabled) cannot be summarised.")
            return
        transcript, clipped = truncate_words(transcript, MAX_WORDS)
        st.session_state.yt = {
            "video_id": video_id,
            "transcript": transcript,
            "clipped": clipped,
            "summary": None,
            "messages": [],
        }

    state = st.session_state.get("yt")
    if not state:
        st.caption("Tip: any public video with captions works, including auto-generated ones.")
        return

    video_col, text_col = st.columns([1, 1])
    with video_col:
        st.video(f"https://www.youtube.com/watch?v={state['video_id']}")
    with text_col:
        st.caption(
            f"Transcript: {word_count(state['transcript']):,} words"
            + (" (clipped)" if state["clipped"] else "")
        )
        with st.container(height=300):
            st.write(state["transcript"])
        st.download_button(
            "⬇️ Download transcript",
            state["transcript"],
            file_name=f"{state['video_id']}_transcript.txt",
            mime="text/plain",
            use_container_width=True,
        )

    st.subheader("📝 Summary")
    if state["summary"]:
        st.markdown(state["summary"])
    elif st.button("Generate summary", type="primary"):
        summary = stream_to_ui(client.complete_stream(SUMMARY_PROMPT, state["transcript"]))
        if summary:
            state["summary"] = summary
            st.rerun()

    st.subheader("💬 Ask about the video")
    for message in state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if question := st.chat_input("What did they say about...?"):
        state["messages"].append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            system = CHAT_PROMPT.format(transcript=state["transcript"])
            reply = stream_to_ui(
                client.stream([{"role": "system", "content": system}, *state["messages"]])
            )
        if reply:
            state["messages"].append({"role": "assistant", "content": reply})
        else:
            state["messages"].pop()
