import streamlit as st
from PIL import Image
from tools.image_utils import image_to_latex

st.title("Image to LaTeX Converter")

# File uploader
uploaded_file = st.file_uploader(
    "Upload an image of a mathematical equation", type=["png", "jpg", "jpeg"]
)

if uploaded_file is not None:
    # Display the uploaded image
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image")

    # Save the uploaded image to a temporary location
    with open("temp_image.png", "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Convert the image to LaTeX code
    with st.spinner("Converting image to LaTeX..."):
        latex_code = image_to_latex("temp_image.png", model="nougat")

    st.subheader("Generated LaTeX Code")
    st.code(latex_code, language="latex")

    st.subheader("Rendered LaTeX Equation")
    st.latex(latex_code)
