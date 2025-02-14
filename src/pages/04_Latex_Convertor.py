import streamlit as st
from pix2tex.cli import LatexOCR
from PIL import Image

def latex_convertor():
    st.title("📝 Latex Convertor")

    # Memory input
    st.write('Upload your image to get the latex code of it')

    uploaded_file = st.file_uploader(
        "choose file:", type=["png", "jpeg", "jpg"], label_visibility="hidden"
    )


    if uploaded_file is not None:
        uploaded_file = Image.open(uploaded_file)
        st.image(uploaded_file)
        model = LatexOCR()
        st.code(model(uploaded_file), language="latex")


latex_convertor()