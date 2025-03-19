import json
import re
from typing import Generator, Union, List, Dict, Any, Optional
from dataclasses import dataclass
from g4f.client import Client

@dataclass
class Message:
    role: str
    content: str

class LLMClient:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.client = Client()
        self.model = model

    def create_messages(self, system_prompt: str, user_prompt: Optional[str] = None) -> List[Dict[str, str]]:
        """Create a list of messages for the LLM."""
        messages = [{"role": "system", "content": system_prompt}]
        if user_prompt:
            messages.append({"role": "user", "content": user_prompt})
        return messages

    def generate_text(
        self,
        system_prompt: str,
        user_prompt: Optional[str] = None,
        stream: bool = False,
    ) -> Union[str, Generator]:
        """
        Generate text using g4f API.

        Args:
            system_prompt (str): The system prompt for the AI.
            user_prompt (str, optional): The user prompt. Defaults to None.
            stream (bool): Whether to stream the response. Defaults to False.

        Returns:
            Union[str, Generator]: A string if not streaming, a generator if streaming.
        """
        messages = self.create_messages(system_prompt, user_prompt)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=stream,
            )
            if stream:
                return response
            return response.choices[0].message.content
        except Exception as e:
            error_msg = f"Error in g4f API call: {str(e)}"
            if stream:
                def error_gen():
                    yield error_msg
                return error_gen()
            return error_msg

    def stream_content(self, response: Generator) -> Generator:
        """
        Process a streaming response from g4f.

        Args:
            response (Generator): The streaming response object from g4f.

        Yields:
            str: Chunks of content from the response.
        """
        for chunk in response:
            delta = chunk.choices[0].delta.content
            if delta is not None:
                yield delta

    def json_output(self, response: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Convert AI response into JSON, with fallback to a default dictionary.

        Args:
            response (str): The raw response from the AI.
            default (dict, optional): Default dict to return if parsing fails. Defaults to None.

        Returns:
            dict: Parsed JSON or default if parsing fails.
        """
        if not response or response.startswith("Error:"):
            return default if default is not None else {}

        # Clean the response
        cleaned = self.remove_triple_backticks(response).strip()
        if not cleaned:
            return default if default is not None else {}

        # Try to find valid JSON block
        try:
            start = cleaned.index("{")
            end = cleaned.rindex("}") + 1
            json_str = cleaned[start:end]
            return json.loads(json_str)
        except (ValueError, json.JSONDecodeError):
            # Fallback: Attempt to fix common issues
            cleaned = cleaned.replace("'", '"').replace("None", '"None"')
            cleaned = re.sub(r",\s*}", "}", cleaned)  # Remove trailing commas
            cleaned = re.sub(r",\s*\]", "]", cleaned)  # Remove trailing commas in lists
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError as e:
                print(f"JSON parsing failed: {e}, Response: {cleaned}")
                return default if default is not None else {}

    @staticmethod
    def remove_triple_backticks(text: str) -> str:
        """
        Removes triple backticks from the beginning and end of a string, if present.

        Args:
            text (str): The input string.

        Returns:
            str: The string with triple backticks removed.
        """
        if text.startswith("```json"):
            text = text[7:]  # Remove ```json
        elif text.startswith("```"):
            text = text[3:]  # Remove ```
        if text.endswith("```"):
            text = text[:-3]  # Remove trailing ```
        return text.strip()

# Create a default client instance
default_client = LLMClient()

# Export commonly used functions for backward compatibility
generate_text = default_client.generate_text
stream_content = default_client.stream_content
json_output = default_client.json_output
remove_triple_backticks = LLMClient.remove_triple_backticks
