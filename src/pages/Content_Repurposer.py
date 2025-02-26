import streamlit as st
from tools.llm_utils import generate_text, stream_content

def main():
    """Content Repurposer App."""

    st.title("📑 Content Repurposer 🔄")
    st.write("✨ Transform your content for different social media platforms. ✨")


    input_text = st.text_area("✍️ Paste your content here:", height=250)
    tone = st.selectbox("🎭 Select Tone:", ("Casual", "Professional", "Humorous"))
    social_media = st.selectbox("📱 Select Social Media:", ("LinkedIn", "Twitter"))

    if st.button("🚀 Generate Repurposed Content"):
        if input_text:
            with st.spinner("🔄 Repurposing content..."):
                if social_media == "LinkedIn":
                    system_prompt = f"""
                    You are an expert in repurposing content for LinkedIn. 
                    Given the following text, create a LinkedIn post that maintains a {tone} tone. 
                    Include relevant hashtags and emojis to enhance engagement. 
                    Focus on delivering a clear and concise message directly derived from the input text.
                    Only use information from the provided text. Do not hallucinate or add any other information.
                    Just give me the final text to put in my linkedin.
                    """
                elif social_media == "Twitter":
                    system_prompt = f"""
                    You are an expert in repurposing content for Twitter. 
                    Given the following text, create a tweet (maximum 280 characters) that maintains a {tone} tone. 
                    Include relevant hashtags. 
                    Focus on delivering a clear and concise message directly derived from the input text.
                    Only use information from the provided text. Do not hallucinate or add any other information.
                    """
                user_prompt = f"""Just give me the revised version of the text in the triple backticks to put in my {social_media}\n
                ```
                {input_text}
                ```"""
                output = st.write_stream(stream_content(generate_text(system_prompt, user_prompt, stream=True)))
                st.session_state.output = output  # Store in session state
        else:
            st.warning("⚠️ Please paste some content to repurpose. ⚠️")

if __name__ == '__main__':
    main()