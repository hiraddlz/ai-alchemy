from g4f.client import Client

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
    from PIL import Image
    
    try:
        image = Image.open(image_url)
        results = pytesseract.image_to_string(image, config = r'--psm 3 -c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz "',
)
        return results
    except Exception as e:
        return f"Error: {e}"