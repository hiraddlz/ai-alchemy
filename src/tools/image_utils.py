from PIL import Image
from tools.llm_utils import LLMClient

# Initialize the LLM client
llm_client = LLMClient()


def generate_image(prompt: str) -> str:
    try:
        response = llm_client.client.images.generate(
            prompt=prompt,
            # n=1,
            # size="512x512"  # You can adjust the size as needed (e.g., "1024x1024")
            response_format="url",
            model="flux",
        )
        image_url = response["data"][0]["url"]
        return image_url
    except Exception as e:
        return f"Error: {e}"


def ocr(image_url: str, language: str = "en") -> str:
    import pytesseract

    try:
        image = Image.open(image_url)
        results = pytesseract.image_to_string(
            image,
            config=r'--psm 3 -c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789() "',
        )
        return results
    except Exception as e:
        return f"Error: {e}"


def image_to_latex(image_path, model="pix2tex"):
    """
    Convert an image containing a mathematical equation to LaTeX code.

    Args:
        image_path (str): The file path to the image.

    Returns:
        str: The LaTeX code representing the equation.
    """
    if model == "pix2tex":
        from pix2tex.cli import LatexOCR

        # Initialize the OCR model
        model = LatexOCR()
        # Open the image file
        image = Image.open(image_path)

        # Perform OCR to get LaTeX code
        latex_code = model(image)
    elif model == "nougat":
        from nougat import Nougat

        # Initialize the OCR model
        model = Nougat()
        # Open the image file
        image = Image.open(image_path)

        # Perform OCR to get LaTeX code
        latex_code = model.predict(image)
    elif model == "surya":
        from surya import Surya

        # Initialize the OCR model
        model = Surya()
        # Open the image file
        image = Image.open(image_path)

        # Perform OCR to get LaTeX code
        latex_code = model.predict(image)
    return latex_code

    return latex_code
