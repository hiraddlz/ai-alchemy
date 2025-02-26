import streamlit as st

from tools.llm_utils import generate_text


def main():
    """ASCII Art Generator App."""

    st.title("🎨 ASCII Art Generator 🖼️")
    st.write("✨ Describe an object, and AI will create ASCII art for you. ✨")

    with st.form("ascii_artist_form"):
        input_text = st.text_area(
            "✍️ Enter the object you want to draw in ASCII art:",
            height=150,
            value="Dog!",
        )
        submitted = st.form_submit_button("🚀 Generate ASCII Art")

        if submitted:
            if input_text:
                with st.spinner("🔄 Generating ASCII art..."):
                    system_prompt = """I want you to act as an ascii artist. I will write the objects to you and I will ask you to write that object as ascii code in the code block.
                    Write only ascii code. Do not explain about the object you wrote."""
                    ascii_art = generate_text(system_prompt, input_text)
                    st.code(ascii_art, language=None)
            else:
                st.warning("⚠️ Please enter an object to generate ASCII art. ⚠️")


if __name__ == "__main__":
    main()
