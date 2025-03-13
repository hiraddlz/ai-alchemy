import streamlit as st
from tools.llm_utils import LLMClient

# Initialize the LLM client
llm_client = LLMClient()


def main():
    st.title("🌐 LLM Translator 📝")
    st.write(
        "✨ Enter text and select a target language to translate using OpenAI's GPT model. ✨"
    )

    # Input text area for source text.
    text_to_translate = st.text_area("✍️ Enter text to translate:", height=200)

    # Select box for target language.
    target_language = st.selectbox(
        "🌍 Select target language:",
        [
            "Persian",
            "English",
            "Spanish",
            "French",
            "German",
            "Chinese",
            "Japanese",
            "Hindi",
            "Arabic",
            "Russian",
            "Portuguese",
        ],
    )

    if st.button("🚀 Translate"):
        if text_to_translate:
            with st.spinner("🔄 Translating..."):
                system_prompt = f"You are a professional translator. Translate the following text to {target_language}\
                    just give me the translation in language {target_language} without any explanation."
                user_prompt = f"This is the text:```{text_to_translate}```\n Just translate the text I gave you in triple backticks to {target_language} language"
                translation = llm_client.generate_text(system_prompt, user_prompt, stream=True)

                st.subheader("✨ Translation:")

                if target_language == "Persian" or target_language == "Arabic":
                    # Apply right-to-left direction for Persian and Arabic
                    st.markdown(
                        f'<div style="direction: rtl; text-align: right;">{ "".join(llm_client.stream_content(translation))}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    # Default left-to-right direction
                    st.write_stream(llm_client.stream_content(translation))

        else:
            st.warning("⚠️ Please enter some text to translate. ⚠️")


if __name__ == "__main__":
    main()
