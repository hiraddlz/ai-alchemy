"""Provider presets and settings resolution.

Settings are resolved in priority order:
    1. values the user typed into the sidebar (``st.session_state``)
    2. ``st.secrets`` (``.streamlit/secrets.toml`` or Streamlit Cloud secrets)
    3. environment variables
    4. provider defaults

Every provider is accessed through the OpenAI-compatible chat completions API, so
adding a new one is a matter of adding a preset below.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Provider:
    key: str
    name: str
    base_url: str | None
    default_model: str
    suggested_models: tuple[str, ...]
    needs_api_key: bool = True
    keys_url: str | None = None
    supports_json_mode: bool = True


PROVIDERS: dict[str, Provider] = {
    "openai": Provider(
        key="openai",
        name="OpenAI",
        base_url=None,
        default_model="gpt-4o-mini",
        suggested_models=("gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1"),
        keys_url="https://platform.openai.com/api-keys",
    ),
    "groq": Provider(
        key="groq",
        name="Groq",
        base_url="https://api.groq.com/openai/v1",
        default_model="llama-3.3-70b-versatile",
        suggested_models=(
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "meta-llama/llama-4-scout-17b-16e-instruct",
        ),
        keys_url="https://console.groq.com/keys",
    ),
    "openrouter": Provider(
        key="openrouter",
        name="OpenRouter",
        base_url="https://openrouter.ai/api/v1",
        default_model="openai/gpt-4o-mini",
        suggested_models=(
            "openai/gpt-4o-mini",
            "anthropic/claude-3.5-haiku",
            "google/gemini-2.0-flash-001",
            "meta-llama/llama-3.3-70b-instruct:free",
        ),
        keys_url="https://openrouter.ai/keys",
    ),
    "gemini": Provider(
        key="gemini",
        name="Google Gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        default_model="gemini-2.0-flash",
        suggested_models=("gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-pro"),
        keys_url="https://aistudio.google.com/apikey",
    ),
    "ollama": Provider(
        key="ollama",
        name="Ollama (local)",
        base_url="http://localhost:11434/v1",
        default_model="llama3.2",
        suggested_models=("llama3.2", "llama3.1", "qwen2.5", "llava"),
        needs_api_key=False,
        keys_url="https://ollama.com/download",
        supports_json_mode=False,
    ),
    "custom": Provider(
        key="custom",
        name="Custom (OpenAI-compatible)",
        base_url=None,
        default_model="",
        suggested_models=(),
        supports_json_mode=False,
    ),
}

DEFAULT_PROVIDER = "openai"

# Names of the settings as they appear in secrets / environment variables.
SETTING_KEYS = ("LLM_PROVIDER", "LLM_API_KEY", "LLM_MODEL", "LLM_BASE_URL")


@dataclass(frozen=True)
class LLMSettings:
    provider: Provider
    api_key: str
    model: str
    base_url: str | None
    temperature: float = 0.3

    @property
    def is_configured(self) -> bool:
        """True when there is enough information to make an API call."""
        if not self.model:
            return False
        if self.provider.needs_api_key and not self.api_key:
            return False
        if self.provider.key == "custom" and not self.base_url:
            return False
        return True


def _first(*values: Any) -> str:
    """Return the first non-empty value as a stripped string."""
    for value in values:
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def resolve_settings(
    overrides: Mapping[str, Any] | None = None,
    secrets: Mapping[str, Any] | None = None,
    env: Mapping[str, str] | None = None,
) -> LLMSettings:
    """Merge the settings sources into a single :class:`LLMSettings`.

    Pure function - Streamlit specific lookups happen in :func:`load_settings`.
    """
    overrides = overrides or {}
    secrets = secrets or {}
    env = os.environ if env is None else env

    def pick(name: str) -> str:
        return _first(overrides.get(name), secrets.get(name), env.get(name))

    provider_key = pick("LLM_PROVIDER").lower() or DEFAULT_PROVIDER
    provider = PROVIDERS.get(provider_key, PROVIDERS["custom"])

    # OPENAI_API_KEY is honoured as a convenience for the default provider.
    api_key = pick("LLM_API_KEY")
    if not api_key and provider.key == "openai":
        api_key = _first(secrets.get("OPENAI_API_KEY"), env.get("OPENAI_API_KEY"))

    model = pick("LLM_MODEL") or provider.default_model
    base_url = pick("LLM_BASE_URL") or provider.base_url

    temperature_raw = _first(overrides.get("LLM_TEMPERATURE"))
    temperature = float(temperature_raw) if temperature_raw else 0.3

    return LLMSettings(
        provider=provider,
        api_key=api_key,
        model=model,
        base_url=base_url or None,
        temperature=temperature,
    )


def _streamlit_secrets() -> Mapping[str, Any]:
    """Return ``st.secrets`` as a plain mapping, tolerating a missing secrets file."""
    try:
        import streamlit as st

        return {
            key: st.secrets[key] for key in (*SETTING_KEYS, "OPENAI_API_KEY") if key in st.secrets
        }
    except Exception:  # no secrets file, or running outside Streamlit
        return {}


def load_settings() -> LLMSettings:
    """Resolve settings inside a running Streamlit app."""
    import streamlit as st

    overrides = {key: st.session_state.get(key) for key in (*SETTING_KEYS, "LLM_TEMPERATURE")}
    return resolve_settings(overrides=overrides, secrets=_streamlit_secrets())
