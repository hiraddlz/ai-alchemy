import streamlit as st
from tools.image_utils import generate_image

import streamlit as st
import openai

TOOL_NAME = "Image Generator"

def main():
    st.title("Image Generator")
    st.write("Enter a prompt to generate an image using OpenAI's DALL·E API.")
    
    prompt = st.text_input("Prompt:")
    if st.button("Generate Image"):
        if prompt:
            with st.spinner("Generating image..."):
                image_url = generate_image(prompt)
                print(image_url)
                st.write(image_url)
            if image_url:
                st.image(image_url, caption=f"Image generated for: {prompt}")
            else:
                st.error("Failed to generate image. Please try again.")
        else:
            st.warning("Please enter a prompt.")


if __name__ == "__main__":
    main()
