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
    from paddleocr import PaddleOCR
    try:
        print(image_url)
        ocr = PaddleOCR(lang=language)
        print(image_url)
        results = ocr.ocr(image_url)
        print('hello')

        print(results)
        results = [line[1][0] for line in results[0]]
        results = " ".join(results)
        return results
    except Exception as e:
        return f"Error: {e}"