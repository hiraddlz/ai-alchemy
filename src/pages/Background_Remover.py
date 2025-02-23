import streamlit as st
from PIL import Image
from rembg import remove
import io

# Set page config
st.set_page_config(page_title="Background Remover", layout="wide")

# App title
st.title("Background Remover App")
st.write("Upload an image to remove the background")


# Function to process the image
def process_image(uploaded_image):
    # Read the image
    input_image = uploaded_image.read()

    # Remove background
    output_image = remove(input_image)

    # Convert to PIL Image
    output_image = Image.open(io.BytesIO(output_image))

    return output_image


# File uploader
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Display original and processed images side by side
    col1, col2 = st.columns(2)

    with col1:
        st.header("Original Image")
        st.image(uploaded_file, use_container_width=True)

    with col2:
        st.header("Processed Image")
        with st.spinner("Removing background..."):
            processed_image = process_image(uploaded_file)
            st.image(processed_image, use_container_width=True)

    # Download button for processed image
    buf = io.BytesIO()
    processed_image.save(buf, format="PNG")
    byte_im = buf.getvalue()

    st.download_button(
        label="Download Processed Image",
        data=byte_im,
        file_name="no_bg.png",
        mime="image/png",
    )
