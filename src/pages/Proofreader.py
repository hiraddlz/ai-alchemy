import streamlit as st
from tools.llm_utils import generate_text, stream_content


def proofreader():
    st.title("📝 Proofreader")
    st.subheader("Correct spelling, grammar, and punctuation errors in the text.")

    # Memory input
    with st.form("proofreder_form"):
        input_text = st.text_area("Add text to correct errors:")
        if st.form_submit_button("Correction"):
            system_prompt = "I want to improve my English. I want you act as a proofreader. I will provide you texts and I would like you to review them for any spelling, grammar, or punctuation errors. just correct the mistakes in my text by changing them to the corrected one.\
                just give me the corrected version of the input text. "
            result = generate_text(system_prompt, input_text, stream=False)

            from redlines import Redlines

            diff = Redlines(input_text, result)
            st.markdown(diff.output_markdown, unsafe_allow_html=True)

            # st.write("Corrected Text")
            # st.write_stream(stream_content(result))


proofreader()
