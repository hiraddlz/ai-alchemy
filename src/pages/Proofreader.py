import streamlit as st
from redlines import Redlines
from tools.llm_utils import LLMClient

# Initialize the LLM client
llm_client = LLMClient()


def proofreader():
    st.title("📝 Proofreader & Editor")
    st.subheader(
        "Instantly correct spelling, grammar, and punctuation errors. See the changes highlighted."
    )

    with st.form("proofreader_form"):
        input_text = st.text_area(
            "Enter text to be proofread:",
            height=200,
            placeholder="Type or paste your text here...",
        )
        if st.form_submit_button("Proofread & Correct"):
            if not input_text.strip():
                st.warning("Please enter some text to proofread.")
                return

            with st.spinner("Proofreading and correcting..."):
                system_prompt = "I want to improve my English. I want you act as a proofreader. I will provide you texts and I would like you to review them for any spelling, grammar, or punctuation errors. Just correct the mistakes in my text by changing them to the corrected one."
                user_prompt = f"This is the input text in the triple backticks: ```{input_text}``` \n Only give me the corrected version of the input text in the triple backticks."

                # Stream the corrected text
                st.markdown("### ✨ Corrected Text:")
                corrected_text = st.write_stream(
                    llm_client.stream_content(
                        llm_client.generate_text(system_prompt, user_prompt, stream=True)
                    )
                )
                corrected_text = llm_client.remove_triple_backticks(corrected_text)

                # Generate and display the diff
                with st.expander("## 🔍 See Changes Highlighted"):
                    diff = Redlines(input_text, corrected_text)
                    st.markdown(diff.output_markdown, unsafe_allow_html=True)


if __name__ == "__main__":
    proofreader()
