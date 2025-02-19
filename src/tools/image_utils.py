from g4f.client import Client
from PIL import Image

client = Client()


def generate_image(prompt: str) -> str:
    try:
        response = client.images.generate(
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

def ocr(image_url: str, language: str ='en') -> str:
    import pytesseract
    
    try:
        image = Image.open(image_url)
        results = pytesseract.image_to_string(image, config = r'--psm 3 -c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789() "',
)
        return results
    except Exception as e:
        return f"Error: {e}"
    

def image_to_latex(image_path):
    """
    Convert an image containing a mathematical equation to LaTeX code.

    Args:
        image_path (str): The file path to the image.

    Returns:
        str: The LaTeX code representing the equation.
    """
    from pix2tex.cli import LatexOCR

    # Initialize the OCR model
    model = LatexOCR()
    # Open the image file
    image = Image.open(image_path)

    # Perform OCR to get LaTeX code
    latex_code = model(image)

    return latex_code