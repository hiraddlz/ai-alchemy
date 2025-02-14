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

        if st.button("Generate"):
            with st.spinner("Repurposing content..."):
                system_prompt = """You're a professional content repurposing expert. 
                Generate A 280-character tweet with hashtags
                Keep tone: {tone}""".format(
                    tone=st.session_state.tone
                )
                st.session_state.output = generate_text(system_prompt, input_text)

    with col2:
        if "output" in st.session_state:
            output_parts = st.session_state.output.split("\n\n")

            with st.expander("Twitter Post", expanded=True):
                st.write(output_parts[0])
                st.button("📋 Copy", key="copy_tweet")


content_repurposer()
