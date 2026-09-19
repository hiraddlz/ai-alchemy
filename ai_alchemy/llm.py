"""Thin, provider-agnostic wrapper around the OpenAI-compatible chat API."""

from __future__ import annotations

import base64
import json
import re
from collections.abc import Callable, Iterator
from typing import Any

from openai import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    NotFoundError,
    OpenAI,
    RateLimitError,
)

from ai_alchemy.config import LLMSettings
from ai_alchemy.free_backend import FreeBackend, FreeProviderError

Message = dict[str, Any]


class LLMError(RuntimeError):
    """A user-presentable error raised for any failed model call."""


def _friendly_error(exc: Exception, settings: LLMSettings) -> LLMError:
    provider = settings.provider.name
    if settings.is_free or isinstance(exc, FreeProviderError):
        detail = str(exc).split(";")[0][:160]
        return LLMError(
            "The free public endpoints could not answer right now "
            f"({detail}). Try again in a moment, pick another free model, or paste your own "
            "key in the sidebar for a reliable provider."
        )
    if isinstance(exc, AuthenticationError):
        return LLMError(f"{provider} rejected the API key. Check it in the sidebar settings.")
    if isinstance(exc, NotFoundError):
        return LLMError(
            f"Model `{settings.model}` was not found on {provider}. Pick another model in the sidebar."
        )
    if isinstance(exc, RateLimitError):
        return LLMError(f"{provider} rate limit or quota exceeded. Wait a moment and try again.")
    if isinstance(exc, APIConnectionError):
        return LLMError(
            f"Could not reach {provider}"
            + (f" at `{settings.base_url}`" if settings.base_url else "")
            + ". Check the base URL and your network connection."
        )
    if isinstance(exc, APIStatusError):
        return LLMError(f"{provider} returned HTTP {exc.status_code}: {exc.message}")
    return LLMError(f"Unexpected error while calling {provider}: {exc}")


def image_to_data_url(data: bytes, mime_type: str = "image/png") -> str:
    """Encode raw image bytes as a ``data:`` URL suitable for vision models."""
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def strip_code_fences(text: str) -> str:
    """Remove a surrounding Markdown code fence (```lang ... ```) if present."""
    text = text.strip()
    match = re.match(r"^```[\w+-]*\s*\n?(.*?)\n?```$", text, flags=re.DOTALL)
    return match.group(1).strip() if match else text


def parse_json_response(text: str) -> dict[str, Any]:
    """Extract the first JSON object from a model response.

    Models frequently wrap JSON in code fences or add a sentence of prose; this
    tolerates both. Raises :class:`LLMError` if no object can be decoded.
    """
    cleaned = strip_code_fences(text)
    candidates = [cleaned]
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start != -1 and end > start:
        candidates.append(cleaned[start : end + 1])

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            # Common LLM slip: trailing commas before a closing bracket.
            candidate = re.sub(r",\s*([}\]])", r"\1", candidate)
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError:
                continue
        if isinstance(parsed, dict):
            return parsed
    raise LLMError("The model did not return valid JSON. Try again or switch to a stronger model.")


class LLMClient:
    """Chat-completion helper shared by every tool.

    Works with any endpoint that speaks the OpenAI chat completions protocol
    (OpenAI, Groq, OpenRouter, Gemini, Ollama, vLLM, LM Studio...).
    """

    def __init__(
        self,
        settings: LLMSettings,
        *,
        before_request: Callable[[list[Message]], None] | None = None,
        **client_kwargs: Any,
    ):
        """``before_request`` runs before every API call and may raise :class:`LLMError`
        (used for shared-mode usage caps)."""
        self.settings = settings
        self._before_request = before_request
        if settings.provider.backend == "g4f":
            self._client: Any = FreeBackend(**client_kwargs)  # client=... in tests
            return
        options: dict[str, Any] = {
            "api_key": settings.api_key or "not-needed",
            "base_url": settings.base_url,
            "timeout": 90,
            "max_retries": 2,
        }
        options.update(client_kwargs)  # e.g. max_retries=0 or http_client=... in tests
        self._client = OpenAI(**options)

    @property
    def model(self) -> str:
        return self.settings.model

    # ------------------------------------------------------------------ core
    def chat(
        self,
        messages: list[Message],
        *,
        temperature: float | None = None,
        json_mode: bool = False,
        max_tokens: int | None = None,
    ) -> str:
        """Return the full assistant reply for ``messages``."""
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.settings.temperature if temperature is None else temperature,
        }
        if max_tokens:
            kwargs["max_tokens"] = max_tokens
        if json_mode and self.settings.provider.supports_json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        if self._before_request:
            self._before_request(messages)
        try:
            response = self._client.chat.completions.create(**kwargs)
        except Exception as exc:  # noqa: BLE001 - converted to a user-facing error
            raise _friendly_error(exc, self.settings) from exc
        content = response.choices[0].message.content if response.choices else None
        if not content:
            raise LLMError("The model returned an empty response.")
        return content

    def stream(self, messages: list[Message], *, temperature: float | None = None) -> Iterator[str]:
        """Yield the assistant reply incrementally."""
        if self._before_request:
            self._before_request(messages)
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.settings.temperature if temperature is None else temperature,
                stream=True,
            )
            for chunk in response:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except Exception as exc:  # noqa: BLE001
            raise _friendly_error(exc, self.settings) from exc

    # ----------------------------------------------------------- convenience
    @staticmethod
    def build_messages(system: str, user: str | list[Message]) -> list[Message]:
        """Build a two-message conversation; ``user`` may be multimodal content."""
        return [{"role": "system", "content": system}, {"role": "user", "content": user}]

    def complete(self, system: str, user: str, **kwargs: Any) -> str:
        return self.chat(self.build_messages(system, user), **kwargs)

    def complete_stream(self, system: str, user: str, **kwargs: Any) -> Iterator[str]:
        return self.stream(self.build_messages(system, user), **kwargs)

    def complete_json(self, system: str, user: str, **kwargs: Any) -> dict[str, Any]:
        """Ask for JSON and parse it, retrying once if the output is malformed."""
        system = system.rstrip() + "\n\nRespond with a single JSON object and nothing else."
        last_error: LLMError | None = None
        for _ in range(2):
            raw = self.chat(self.build_messages(system, user), json_mode=True, **kwargs)
            try:
                return parse_json_response(raw)
            except LLMError as exc:
                last_error = exc
        assert last_error is not None
        raise last_error

    def describe_image(
        self,
        prompt: str,
        image_bytes: bytes,
        mime_type: str = "image/png",
        *,
        system: str = "You are a precise assistant that reads images.",
        **kwargs: Any,
    ) -> str:
        """Send an image plus a text prompt to a vision-capable model."""
        content: list[Message] = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image_to_data_url(image_bytes, mime_type)}},
        ]
        return self.chat(self.build_messages(system, content), **kwargs)

    def ping(self) -> str:
        """Make the cheapest possible call to verify the configuration."""
        return self.chat(
            [{"role": "user", "content": "Reply with the single word: pong"}],
            temperature=0,
            max_tokens=5,
        )
