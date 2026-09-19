"""Shared Streamlit UI helpers used by every page."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import streamlit as st

from ai_alchemy.config import PROVIDERS, LLMSettings, load_settings
from ai_alchemy.llm import LLMClient, LLMError
from ai_alchemy.quota import demo_guard

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
REPO_URL = "https://github.com/hiraddlz/ai-alchemy"


def load_css() -> None:
    css_path = ASSETS_DIR / "style.css"
    if css_path.exists():
        st.html(f"<style>{css_path.read_text(encoding='utf-8')}</style>")


def page_header(title: str, icon: str, description: str) -> None:
    st.title(f"{icon} {title}")
    st.caption(description)


# ------------------------------------------------------------------ settings
def render_settings_sidebar() -> LLMSettings:
    """Render the provider/model/key controls and return the resolved settings."""
    settings = load_settings()
    provider_keys = list(PROVIDERS)

    with st.sidebar:
        title = "⚙️ Model settings" + (" (optional)" if settings.is_shared else "")
        with st.expander(title, expanded=not settings.is_configured):
            if settings.is_shared:
                st.caption(
                    "A free shared model is preloaded. Paste your own key to pick any model "
                    "and remove the demo limits."
                )
            provider_key = st.selectbox(
                "Provider",
                provider_keys,
                index=provider_keys.index(settings.provider.key),
                format_func=lambda key: PROVIDERS[key].name,
                key="LLM_PROVIDER",
            )
            provider = PROVIDERS[provider_key]

            if provider.needs_api_key:
                st.text_input(
                    "API key",
                    type="password",
                    key="LLM_API_KEY",
                    placeholder="Paste your key (kept in this session only)",
                    help=f"Get a key at {provider.keys_url}" if provider.keys_url else None,
                )
            if provider.key == "custom":
                st.text_input("Base URL", key="LLM_BASE_URL", placeholder="https://host/v1")

            # Reset the model field when the provider changes so its default applies.
            if st.session_state.get("_last_provider") != provider_key:
                st.session_state["_last_provider"] = provider_key
                st.session_state["LLM_MODEL"] = (
                    settings.model
                    if settings.provider.key == provider_key
                    else provider.default_model
                )
            settings = load_settings()
            st.text_input(
                "Model",
                key="LLM_MODEL",
                disabled=settings.is_shared,
                help=(
                    "Locked while using the shared key - paste your own key to change it."
                    if settings.is_shared
                    else "Suggestions: " + ", ".join(provider.suggested_models)
                    if provider.suggested_models
                    else "Any chat model served by your endpoint."
                ),
            )
            st.slider("Creativity (temperature)", 0.0, 1.0, 0.3, 0.05, key="LLM_TEMPERATURE")

            settings = load_settings()
            if st.button(
                "Test connection", use_container_width=True, disabled=not settings.is_configured
            ):
                try:
                    with st.spinner("Pinging model..."):
                        LLMClient(settings).ping()
                    st.success(f"Connected to {settings.provider.name} · `{settings.model}`")
                except LLMError as exc:
                    st.error(str(exc))

        if settings.is_shared:
            used = int(st.session_state.get("demo_calls", 0))
            limit = settings.demo_limit("DEMO_SESSION_LIMIT")
            st.caption(
                f"🟢 Free shared model · `{settings.model}` · {used}/{limit} demo calls used"
            )
        elif settings.is_configured:
            st.caption(f"🟢 {settings.provider.name} · `{settings.model}` · your key")
        else:
            st.caption("🔴 Not configured - add a key above")
        st.caption(
            "Keys stay in your browser session and are never stored. "
            f"[Source on GitHub]({REPO_URL})"
        )
    return settings


def require_client() -> LLMClient:
    """Return a ready client, or stop the page with a friendly prompt to configure one."""
    settings = load_settings()
    if not settings.is_configured:
        st.info(
            "This tool needs a language model. Open **⚙️ Model settings** in the sidebar, "
            "pick a provider and paste an API key (free tiers exist for Groq, OpenRouter and Gemini).",
            icon="🔑",
        )
        st.stop()
    if settings.is_shared:
        return LLMClient(settings, before_request=demo_guard(settings))
    return LLMClient(settings)


# ------------------------------------------------------------------ helpers
def stream_to_ui(chunks: Iterator[str]) -> str | None:
    """Stream text into the page; show the error and return ``None`` on failure."""
    try:
        return st.write_stream(chunks)  # type: ignore[return-value]
    except LLMError as exc:
        st.error(str(exc))
        return None


def show_error(exc: Exception) -> None:
    st.error(str(exc) if isinstance(exc, LLMError) else f"Something went wrong: {exc}")


def example_button(label: str, key: str, text: str) -> None:
    """A small button that fills the widget identified by ``key`` with sample content.

    The state is set in an ``on_click`` callback because callbacks run before the
    script reruns, which is the only time a widget's session-state value may change.
    """

    def _fill() -> None:
        st.session_state[key] = text

    st.button(label, key=f"{key}__example", type="tertiary", on_click=_fill)


def word_count(text: str) -> int:
    return len(text.split())
