import streamlit as st
from tools.llm_utils import generate_text, stream_content


def proofreader():
    st.title("📝 Proofreader")

    # Memory input
    with st.form("proofreder_form"):
        input_text = st.text_area("Add text to correct errors:")
        if st.form_submit_button("Correction"):
            system_prompt = "I want you act as a proofreader. I will provide you texts and I would like you to review them for any spelling, grammar, or punctuation errors. Once you have finished reviewing the text, provide me with any necessary corrections or suggestions for improve the text."
            result = generate_text(system_prompt, input_text, stream=True)
            st.write("Corrected Text")
            st.write_stream(stream_content(result))


proofreader()
