import streamlit as st
from tools.llm_utils import generate_text


def main():
    st.title("LLM Translator")
    st.write(
        "Enter text and select a target language to translate using OpenAI's GPT model."
    )

    # Input text area for source text.
    text_to_translate = st.text_area("Enter text to translate:", height=200)

    # Select box for target language.
    target_language = st.selectbox(
        "Select target language",
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

    if st.button("Translate"):
        if text_to_translate:
            with st.spinner("Translating..."):
                system_prompt = f"You are a professional translator. Translate the following text to {target_language}\
                    just give me the translation in language {target_language} without any explanation."
                translation = generate_text(system_prompt, text_to_translate)
            st.subheader("Translation")
            st.write(translation)
        else:
            st.warning("Please enter some text to translate.")


if __name__ == "__main__":
    main()
