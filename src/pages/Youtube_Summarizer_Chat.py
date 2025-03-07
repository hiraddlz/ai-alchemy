import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from tools.llm_utils import generate_text, stream_content
from g4f.client import Client

client = Client()

# Define the display name of the tool
TOOL_NAME = "YouTube Video Summarizer & Chat 🎬"


def extract_video_id(url: str) -> str:
    """Extracts the YouTube video ID from a URL."""
    parsed_url = urlparse(url)

    if parsed_url.hostname in ["www.youtube.com", "youtube.com"]:
        query_params = parse_qs(parsed_url.query)
        video_id = query_params.get("v")
        if video_id:
            return video_id[0]
    elif parsed_url.hostname == "youtu.be":
        # Handle youtu.be short links
        video_id = parsed_url.path.lstrip("/")
        if video_id:
            return video_id

    return None


def fetch_transcript(video_id: str) -> str:
    """Fetches the transcript for the given YouTube video ID."""
    try:
        transcript_entries = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([entry["text"] for entry in transcript_entries])
        return transcript
    except Exception as e:
        st.error(f"Error fetching transcript: {str(e)}")
        return None


def summarize_transcript(transcript: str) -> str:
    """Uses the LLM to summarize the provided transcript."""
    system_prompt = "You are a professional summarizer. Provide a concise summary of the provided text."
    user_prompt = f"Summarize the following YouTube video transcript into a concise summary:\n\n{transcript}"
    try:
        # Create a streaming response using the client
        stream = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            stream=True,
        )
        return stream
    except Exception as e:
        st.error(f"Error during summarization: {str(e)}")
        return "An error occurred during summarization."


def display_transcript(transcript):
    """Displays the transcript in a scrollable container."""
    st.subheader("📜 Video Transcript:")
    with st.container():
        st.markdown(
            """
            <div style="height: 200px; overflow-y: auto; border: 1px solid #ccc; padding: 10px;">
                <p>"""
            + transcript
            + """</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def run():
    """Runs the YouTube Video Summarizer & Chat app."""
    st.title("YouTube Video Summarizer & Chat 🎬")
    st.write(
        "✨ Enter a YouTube video URL to get a summary and chat with the transcript. ✨"
    )

    # Initialize session state variables if they don't exist
    if "transcript" not in st.session_state:
        st.session_state.transcript = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_video_id" not in st.session_state:
        st.session_state.current_video_id = None
    if "summary" not in st.session_state:
        st.session_state.summary = None

    url = st.text_input("🔗 YouTube Video URL:")

    if st.button("🚀 Process Video"):
        if url:
            video_id = extract_video_id(url)
            if video_id:
                # Check if this is a new video
                if st.session_state.current_video_id != video_id:
                    # Reset conversation for new video
                    st.session_state.messages = []
                    st.session_state.summary = None
                    st.session_state.current_video_id = video_id

                with st.spinner("🔄 Fetching transcript..."):
                    transcript = fetch_transcript(video_id)
                    if transcript:
                        st.session_state.transcript = transcript
                    else:
                        st.error("⚠️ Could not fetch transcript for this video. ⚠️")
                        return
            else:
                st.error(
                    "⚠️ Invalid YouTube URL. Please check the link and try again. ⚠️"
                )
                return
        else:
            st.warning("⚠️ Please enter a YouTube video URL. ⚠️")
            return

    # Always display transcript if available
    if st.session_state.transcript:
        transcript = st.session_state.transcript
        display_transcript(transcript)

        # Add a horizontal separator
        st.markdown("---")

        st.subheader("📝 Video Summary:")
        if st.button("Generate Summary") or st.session_state.summary:
            with (
                st.spinner("📝 Summarizing transcript...")
                if not st.session_state.summary
                else st.empty()
            ):
                if not st.session_state.summary:
                    summary_stream = summarize_transcript(transcript)
                    st.session_state.summary = st.write_stream(
                        stream_content(summary_stream)
                    )
                else:
                    st.write(st.session_state.summary)

        # Add another horizontal separator
        st.markdown("---")

        st.subheader("💬 Chat with Transcript:")

        # Initialize chat history with system message if empty
        if not st.session_state.messages:
            system_prompt = (
                f"You are a helpful assistant analyzing the following YouTube video transcript:\n\n"
                f"<transcript>\n{transcript}\n</transcript>\n\n"
                f"Please answer questions based only on the information provided in this transcript."
            )
            st.session_state.messages = [{"role": "system", "content": system_prompt}]

        # Display chat history
        for message in st.session_state.messages:
            if message["role"] != "system":  # Don't display the system message
                with st.chat_message(message["role"]):
                    st.write(message["content"])

        # Question input
        question = st.chat_input("Ask something about the video")

        # Handle question and generate response
        if question:
            # Display user message
            with st.chat_message("user"):
                st.write(question)

            # Add user message to history
            st.session_state.messages.append({"role": "user", "content": question})

            # Generate response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    stream = client.chat.completions.create(
                        model="gpt-4",
                        messages=st.session_state.messages,
                        stream=True,
                    )
                    response = st.write_stream(stream_content(stream))

            # Add assistant message to history
            st.session_state.messages.append({"role": "assistant", "content": response})

        # Buttons for chat management
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Clear Chat", use_container_width=True):
                # Reset chat but keep the system message with transcript
                system_message = (
                    st.session_state.messages[0] if st.session_state.messages else None
                )
                st.session_state.messages = [system_message] if system_message else []
                st.rerun()

        with col2:
            if st.button("Start New Video", use_container_width=True):
                # Reset everything
                st.session_state.transcript = None
                st.session_state.messages = []
                st.session_state.current_video_id = None
                st.session_state.summary = None
                st.rerun()


if __name__ == "__main__":
    run()
