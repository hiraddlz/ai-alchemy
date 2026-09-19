"""Landing page: hero + a card per tool."""

from __future__ import annotations

import streamlit as st

from ai_alchemy.config import PROVIDERS, load_settings
from ai_alchemy.registry import TOOLS
from ai_alchemy.ui import REPO_URL


def render() -> None:
    st.html(
        """
        <div class="hero">
          <div class="hero-title">⚗️ AI Alchemy</div>
          <div class="hero-subtitle">
            A dozen AI-powered tools in one place: writing, documents, career, translation and vision -
            powered by whichever LLM provider you bring.
          </div>
        </div>
        """
    )

    settings = load_settings()
    if settings.is_shared:
        st.success(
            "**No setup needed** - a free shared model is preloaded, just pick a tool. "
            "Want a stronger model or no demo limits? Paste your own key in **⚙️ Model settings**.",
            icon="🎁",
        )
    elif settings.is_free:
        st.success(
            "**No setup needed** - free public models (DeepSeek, GLM, Qwen, ...) are ready, "
            "just pick a tool. Prefer a specific provider? Paste your key in **⚙️ Model settings**.",
            icon="🎁",
        )
    elif settings.is_configured:
        st.success(
            f"Ready - using **{settings.provider.name}** with `{settings.model}`. Pick a tool below.",
            icon="✅",
        )
    else:
        st.info(
            "**Get started:** open **⚙️ Model settings** in the sidebar and paste an API key. "
            "Works with OpenAI, Gemini, Groq, DeepSeek, Hugging Face, OpenRouter, a local Ollama "
            "server or any OpenAI-compatible endpoint. The image tools work without a key.",
            icon="👋",
        )

    columns = st.columns(4)
    for index, tool in enumerate(TOOLS):
        with columns[index % 4], st.container(border=True):
            st.markdown(f"### {tool.icon} {tool.title}")
            st.caption(tool.category + ("" if tool.needs_llm else " · no key needed"))
            st.markdown(tool.description)
            st.page_link(
                st.session_state["_pages"][tool.slug],
                label="Open",
                icon="➡️",
                use_container_width=True,
            )

    st.divider()
    left, right = st.columns([3, 2])
    with left:
        st.markdown(
            f"""
            **How it works.** Every tool talks to the model through the OpenAI-compatible chat
            API, so switching providers is a dropdown - no code changes. Structured tasks
            (IELTS grading, resume matching) request JSON and validate it; long outputs stream
            token by token. Image tools run locally in the browser session.

            **Privacy.** Your API key and content live only in your Streamlit session; nothing is
            logged or persisted by this app. Source: [{REPO_URL.removeprefix("https://")}]({REPO_URL})
            """
        )
    with right:
        st.metric("Tools", len(TOOLS))
        st.metric("LLM providers", len(PROVIDERS))
