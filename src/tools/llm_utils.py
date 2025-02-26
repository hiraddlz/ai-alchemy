import json
import re

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


def json_output(answer):
    """
    Convert string output of AI answer into JSON.

    Args:
        answer (str): AI's response.

    Returns:
        dict: JSON representation of the answer.
    """
    start = answer.index("{")
    ends = [match.start() for match in re.finditer("}", answer)]
    if len(ends) == 0:
        ends.append(len(answer))
        answer += "}"
    for end in ends[::-1]:
        try:
            processed_text = answer[start : end + 1]
            return json.loads(processed_text)
        except:
            continue
    processed_text = processed_text.replace("\n", " ")
    processed_text = processed_text.replace("'", '"')
    processed_text = processed_text.replace("None", '"None"')
    processed_text = processed_text.replace("'", '"')
    processed_text = processed_text.replace("\n", "")
    return json.loads(processed_text)


def remove_triple_backticks(text):
    """
    Removes triple backticks from the beginning and end of a string, if present.

    Args:
        text (str): The input string.

    Returns:
        str: The string with triple backticks removed, or the original string if not found.
    """
    if text.startswith("```"):
        text = text[3:]  # Remove leading backticks
    if text.endswith("```"):
        text = text[:-3]  # Remove trailing backticks
    return text.strip()  # Remove any leading or trailing whitespace.
