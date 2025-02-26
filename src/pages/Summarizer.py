import streamlit as st
from tools.llm_utils import generate_text, stream_content


def summarizer():
    """AI Summarizer App."""

    st.title("🧠 AI Text Summarizer 📝")
    st.write("✨ Paste your text below and let AI generate a concise summary. ✨")

    with st.form("summary_form"):
        input_text = st.text_area("✍️ Paste text to summarize:", height=250)
        submitted = st.form_submit_button("🚀 Generate Summary")

        if submitted:
            if input_text:
                with st.spinner("🔄 Summarizing..."):
                    system_prompt = "You are a helpful assistant that creates concise summaries of text."
                    user_prompt = f"Summarize the following text:\n\n{input_text}"
                    summary = generate_text(system_prompt, user_prompt, stream=True)

                    st.subheader("✨ Summary:")
                    st.write_stream(stream_content(summary))
            else:
                st.warning("⚠️ Please paste some text to summarize. ⚠️")


if __name__ == "__main__":
    summarizer()
