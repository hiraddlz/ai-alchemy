from g4f.client import Client

client = Client()


def generate_text(system_prompt: str, user_prompt: str = None, model="gpt-4") -> str:
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