import streamlit as st
from PIL import Image
import io
import pyperclip
import base64


def image_to_ascii(
    image,
    output_width=100,
    grayscale="default",
    invert=False,
    brightness=1.0,
    contrast=1.0,
):
    """
    Converts a PIL Image object to ASCII art with adjustable detail, brightness, and contrast.
    """
    if image is None:
        return ""

    img = image.convert("L")  # Convert to grayscale

    width, height = img.size
    aspect_ratio = height / width
    output_height = int(
        output_width * aspect_ratio * 0.5
    )  # Adjust for character aspect ratio

    img = img.resize((output_width, output_height), resample=Image.LANCZOS)

    pixels = img.getdata()

    if grayscale == "default":
        grayscale_chars = " .:-=+*#%@MW&8Q0X$UOZAJKYP6G9V432F5S7I1TLrcvunxzjft/\|()1{}[]?-_+~<>i!lI;:,\"^`'. "
    elif grayscale == "simple":
        grayscale_chars = " .:-=+*#"
    else:
        grayscale_chars = grayscale

    if invert:
        grayscale_chars = grayscale_chars[::-1]

    num_chars = len(grayscale_chars)
    pixel_range = 256 / num_chars

    ascii_art = ""
    for i, pixel_value in enumerate(pixels):
        # Apply brightness and contrast adjustments
        adjusted_pixel = int(
            min(255, max(0, (pixel_value - 128) * contrast + 128 * brightness))
        )
        ascii_art += grayscale_chars[int(adjusted_pixel / pixel_range)]
        if (i + 1) % output_width == 0:
            ascii_art += "\n"

    return ascii_art


st.title("🖼️ ASCII Art Generator 🎨")

uploaded_file = st.file_uploader("Upload an image 📸", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image ✨", use_container_width=True)

    col1, col2, col3, col4 = st.columns(4)

    output_width = col1.slider("Output Width 📏", 50, 200, 100)
    grayscale_options = ["simple", "detailed", "custom", "custom_detailed"]
    grayscale_type = col2.selectbox("Grayscale Type 🌈", grayscale_options)

    if grayscale_type == "custom":
        custom_chars = col2.text_input("Custom Grayscale Characters ✍️", " .:-=+*#%@")
        grayscale_chars = custom_chars
    elif grayscale_type == "custom_detailed":
        custom_chars = col2.text_input(
            "Custom Detailed Grayscale Characters ✍️",
            " .:-=+*#%@MW&8Q0X$UOZAJKYP6G9V432F5S7I1TLrcvunxzjft/\|()1{}[]?-_+~<>i!lI;:,\"^`'. ",
        )
        grayscale_chars = custom_chars
    else:
        grayscale_chars = grayscale_type

    invert = col3.checkbox("Invert Grayscale 🔄")
    brightness = col3.slider("Brightness ☀️", 0.5, 2.0, 1.0)
    contrast = col4.slider("Contrast 🌓", 0.5, 2.0, 1.0)

    ascii_result = image_to_ascii(
        image, output_width, grayscale_chars, invert, brightness, contrast
    )
    st.code(ascii_result, language=None)

    col5, col6 = st.columns(2)

    if col5.button("Copy to Clipboard 📋"):
        pyperclip.copy(ascii_result)
        st.success("ASCII art copied to clipboard! ✅")

    if col6.download_button(
        label="Save as Text File 💾",
        data=ascii_result.encode("utf-8"),
        file_name="ascii_art.txt",
        mime="text/plain",
    ):
        st.success("File Downloaded! ⬇️")
