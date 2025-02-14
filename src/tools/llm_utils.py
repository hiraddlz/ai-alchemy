from g4f.client import Client

client = Client()


def generate_text(
    system_prompt: str, user_prompt: str = None, model="gpt-4", stream=False
) -> str:
    if stream:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                stream=True,
            )
            return response
        except Exception as e:
            return f"Error: {str(e)}"
    else:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"


def stream_content(response):  # response is a generator
    for chunk in response:
        delta = chunk.choices[0].delta.content
        if delta:  # handle potential None values
            yield delta
