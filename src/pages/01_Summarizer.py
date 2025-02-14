import streamlit as st

from tools.llm_utils import generate_text, stream_content


def summarizer():
    st.title("🧠 AI Summarizer")

    # Memory input
    with st.form("summary_form"):
        input_text = st.text_area("Add text to summarize:")
        if st.form_submit_button("Summarize"):
            system_prompt = "You are a helpful assistant that summarizes text."
            user_prompt = f"Summarize the following text:\n\n{input_text}"
            summary = generate_text(system_prompt, user_prompt, stream=True)
            st.write("### Summary:")
            st.write_stream(stream_content(summary))


summarizer()
