import streamlit as st
from tools.llm_utils import generate_text


def ascii_artist():
    st.title("ASCII Artist")

    # Memory input
    with st.form("ascii_artist_form"):
        input_text = st.text_area("Enter the object you want to draw in ASCII art:")
        if st.form_submit_button("Generate ASCII Art"):
            system_prompt = "I want you to act as an ascii artist. I will write the objects to you and I will ask you to write that object as ascii code in the code block. Write only ascii code. Do not explain about the object you wrote. I will say the objects in double quotes"
            ascii = generate_text(system_prompt, input_text)
            st.code(ascii, language=None)

ascii_artist()