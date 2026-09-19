"""Provider presets and settings resolution.

Settings come from three sources:

* **session** - what the visitor typed into the sidebar (``st.session_state``)
* **host**    - ``st.secrets`` (``.streamlit/secrets.toml`` / Streamlit Cloud) or environment
                variables, i.e. whatever the person deploying the app configured
* provider defaults

A visitor's own key always wins. When no key was typed and the selected provider is the
one the host configured, the host key is used in **shared mode**: the host's model is
locked and :mod:`ai_alchemy.quota` applies usage caps so one visitor cannot exhaust the
host's free tier. Every provider is accessed through the OpenAI-compatible chat API.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal


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
    "gemini": Provider(
        key="gemini",
        name="Google Gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        default_model="gemini-2.0-flash",
        suggested_models=("gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-pro"),
        keys_url="https://aistudio.google.com/apikey",
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

# Shared-mode caps (host-tunable). Defaults suit the Gemini free tier (15 RPM, 1500 RPD).
DEMO_DEFAULTS = {
    "DEMO_SESSION_LIMIT": 25,  # model calls per visitor session
    "DEMO_RPM": 12,  # model calls per minute across all visitors
    "DEMO_MAX_WORDS": 15_000,  # largest prompt accepted in shared mode
}

KeySource = Literal["session", "host", "none"]


@dataclass(frozen=True)
class LLMSettings:
    provider: Provider
    api_key: str
    model: str
    base_url: str | None
    temperature: float = 0.3
    key_source: KeySource = "none"
    demo_limits: Mapping[str, int] | None = None

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

    @property
    def is_shared(self) -> bool:
        """True when the visitor is running on the host's key (usage caps apply)."""
        return self.provider.needs_api_key and self.key_source == "host"

    def demo_limit(self, name: str) -> int:
        return int((self.demo_limits or {}).get(name, DEMO_DEFAULTS[name]))


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

    def host(name: str) -> str:
        return _first(secrets.get(name), env.get(name))

    host_provider_key = host("LLM_PROVIDER").lower() or DEFAULT_PROVIDER
    provider_key = _first(overrides.get("LLM_PROVIDER")).lower() or host_provider_key
    provider = PROVIDERS.get(provider_key, PROVIDERS["custom"])
    on_host_provider = provider_key == host_provider_key

    session_key = _first(overrides.get("LLM_API_KEY"))
    host_key = host("LLM_API_KEY")
    if not host_key and host_provider_key == "openai":
        host_key = host("OPENAI_API_KEY")  # honoured as a convenience

    if session_key:
        api_key, key_source = session_key, "session"
    elif on_host_provider and host_key:
        api_key, key_source = host_key, "host"
    else:
        api_key, key_source = "", "none"

    shared = provider.needs_api_key and key_source == "host"
    if shared:
        # The host's key only ever runs the host's model and endpoint.
        model = host("LLM_MODEL") or provider.default_model
        base_url = host("LLM_BASE_URL") or provider.base_url
    else:
        model = _first(overrides.get("LLM_MODEL")) or (
            host("LLM_MODEL") if on_host_provider else ""
        )
        model = model or provider.default_model
        base_url = _first(overrides.get("LLM_BASE_URL")) or (
            host("LLM_BASE_URL") if on_host_provider else ""
        )
        base_url = base_url or provider.base_url

    temperature_raw = _first(overrides.get("LLM_TEMPERATURE"))
    temperature = float(temperature_raw) if temperature_raw else 0.3

    demo_limits = {name: int(host(name) or default) for name, default in DEMO_DEFAULTS.items()}

    return LLMSettings(
        provider=provider,
        api_key=api_key,
        model=model,
        base_url=base_url or None,
        temperature=temperature,
        key_source=key_source,
        demo_limits=demo_limits,
    )


def _streamlit_secrets() -> Mapping[str, Any]:
    """Return ``st.secrets`` as a plain mapping, tolerating a missing secrets file."""
    try:
        import streamlit as st

        names = (*SETTING_KEYS, "OPENAI_API_KEY", *DEMO_DEFAULTS)
        return {name: st.secrets[name] for name in names if name in st.secrets}
    except Exception:  # no secrets file, or running outside Streamlit
        return {}


def load_settings() -> LLMSettings:
    """Resolve settings inside a running Streamlit app."""
    import streamlit as st

    overrides = {key: st.session_state.get(key) for key in (*SETTING_KEYS, "LLM_TEMPERATURE")}
    return resolve_settings(overrides=overrides, secrets=_streamlit_secrets())
