"""Keyless backend: routes chat completions through public endpoints via ``g4f``.

It exposes the same ``chat.completions.create(...)`` surface as the OpenAI client so
:class:`~ai_alchemy.llm.LLMClient` can use either interchangeably. Requests go to a
curated chain of providers that currently work without authentication; the first one
that answers wins. Quality and availability are best-effort by nature.
"""

from __future__ import annotations

import itertools
from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any

FREE_TIMEOUT = 60  # seconds per attempt
AUTO_MODEL = "kilo-auto/free"


class FreeProviderError(RuntimeError):
    """Every provider in the chain failed."""


def _attempts(model: str) -> list[tuple[Any, str]]:
    """(provider, model) pairs to try in order for the requested ``model``."""
    from g4f.Provider import CohereForAI_C4AI_Command, HuggingSpace, KiloCode

    chain: list[tuple[Any, str]] = [(KiloCode, model)]
    if model != AUTO_MODEL:
        chain.append((KiloCode, AUTO_MODEL))
    chain.append((HuggingSpace, HuggingSpace.default_model))
    chain.append((CohereForAI_C4AI_Command, CohereForAI_C4AI_Command.default_model))
    return chain


def _prime(stream: Iterator[Any]) -> Iterator[Any]:
    """Pull the first chunk so connection failures surface before we commit to a provider."""
    iterator = iter(stream)
    try:
        first = next(iterator)
    except StopIteration as exc:
        raise FreeProviderError("empty response") from exc
    return itertools.chain([first], iterator)


class FreeBackend:
    """OpenAI-client look-alike backed by g4f with provider fallback."""

    def __init__(self, client: Any | None = None):
        if client is None:
            from g4f.client import Client

            client = Client()
        self._client = client
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        stream: bool = False,
        temperature: float | None = None,
        **_ignored: Any,  # max_tokens (starves reasoning models), response_format, ...
    ) -> Any:
        errors: list[str] = []
        for provider, provider_model in _attempts(model):
            try:
                response = self._client.chat.completions.create(
                    model=provider_model,
                    messages=messages,
                    provider=provider,
                    stream=stream,
                    timeout=FREE_TIMEOUT,
                    **({"temperature": temperature} if temperature is not None else {}),
                )
                return _prime(response) if stream else response
            except Exception as exc:  # noqa: BLE001 - try the next provider
                errors.append(f"{getattr(provider, '__name__', provider)}: {exc}")
        raise FreeProviderError("; ".join(errors))
