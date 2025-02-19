import streamlit as st

from tools.llm_utils import generate_text


def content_repurposer():
    st.title("📑 Content Repurposer")

    col1, col2 = st.columns([3, 2])

    with col1:
        input_text = st.text_area("Paste your content here:", height=300)
        st.session_state.tone = st.selectbox(
            "Select Tone:", ("Casual", "Professional", "Humorous")
        )
        st.session_state.social_media = st.selectbox(
            "Select Social Media:", ("Linkedin", "Twitter")
        )

        if st.button("Generate"):
            with st.spinner("Repurposing content..."):
                if st.session_state.social_media == "Linkedin":
                    system_prompt = """You're a professional content repurposing expert. 
                    Generate a LinkedIn post with hashtags and emojis
                    Keep tone: {tone}""".format(
                        tone=st.session_state.tone
                    )

                elif st.session_state.social_media == "Twitter":
                    system_prompt = """You're a professional content repurposing expert. 
                    Generate A 280-character tweet with hashtags
                    Keep tone: {tone}""".format(
                        tone=st.session_state.tone
                    )
                st.session_state.output = generate_text(system_prompt, input_text)

    with col2:
        if "output" in st.session_state:
            with st.expander("Social Media Post", expanded=True):
                st.write(st.session_state.output)
                st.button("📋 Copy", key="copy")


content_repurposer()
