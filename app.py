"""AI Alchemy entry point: ``streamlit run app.py``."""

from __future__ import annotations

import importlib

import streamlit as st

from ai_alchemy import __version__
from ai_alchemy.registry import TOOLS, tools_by_category
from ai_alchemy.ui import ASSETS_DIR, load_css, render_settings_sidebar

st.set_page_config(
    page_title="AI Alchemy",
    page_icon="⚗️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": "https://github.com/hiraddlz/ai-alchemy",
        "Report a bug": "https://github.com/hiraddlz/ai-alchemy/issues",
        "About": f"**AI Alchemy** v{__version__} - a provider-agnostic AI toolkit.",
    },
)
load_css()
st.logo(str(ASSETS_DIR / "logo.svg"), size="large")


def _page(slug: str, title: str, icon: str, default: bool = False) -> st.Page:
    module = importlib.import_module(f"ai_alchemy.pages.{slug}")
    return st.Page(module.render, title=title, icon=icon, url_path=slug, default=default)


pages = {"": [_page("home", "Home", "🏠", default=True)]}
for category, tools in tools_by_category().items():
    pages[category] = [_page(tool.slug, tool.title, tool.icon) for tool in tools]
# Page objects are needed by st.page_link on the home page.
st.session_state["_pages"] = {page.url_path: page for section in pages.values() for page in section}

navigation = st.navigation(pages, position="sidebar", expanded=True)

render_settings_sidebar()
st.sidebar.caption(f"{len(TOOLS)} tools · v{__version__}")

navigation.run()
