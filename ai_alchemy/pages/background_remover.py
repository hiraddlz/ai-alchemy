"""Background removal with rembg (local ONNX model, no API key needed)."""

from __future__ import annotations

import io

import streamlit as st
from PIL import Image

from ai_alchemy.ui import page_header


@st.cache_resource(show_spinner="Loading the segmentation model (first run downloads ~170 MB)...")
def _session():
    from rembg import new_session

    return new_session("u2net")


@st.cache_data(show_spinner=False)
def _remove_background(data: bytes, alpha_matting: bool) -> bytes:
    from rembg import remove

    return remove(data, session=_session(), alpha_matting=alpha_matting)


def _rembg_available() -> bool:
    try:
        import rembg  # noqa: F401
    except ImportError:
        return False
    return True


def render() -> None:
    page_header(
        "Background Remover", "🖼️", "Cut out the subject of a photo locally with a U²-Net model."
    )

    if not _rembg_available():
        st.warning(
            "This tool needs the optional `rembg` package. Install it with "
            '`pip install "ai-alchemy[images]"` (or `pip install rembg[cpu]`) and restart the app.',
            icon="📦",
        )
        return

    uploaded = st.file_uploader("Image", type=["png", "jpg", "jpeg", "webp"])
    if uploaded is None:
        st.info("Works best on photos with a clear subject: people, products, pets.")
        return

    alpha_matting = st.toggle("Alpha matting (finer edges, slower)", value=False)
    background = st.selectbox("Preview background", ["Transparent", "White", "Black", "Green"])

    before, after = st.columns(2)
    with before:
        st.markdown("##### Original")
        st.image(uploaded, use_container_width=True)
    with after:
        st.markdown("##### Result")
        try:
            with st.spinner("Removing background..."):
                result_bytes = _remove_background(uploaded.getvalue(), alpha_matting)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Background removal failed: {exc}")
            return
        result = Image.open(io.BytesIO(result_bytes)).convert("RGBA")

        preview = result
        if background != "Transparent":
            colour = {"White": "white", "Black": "black", "Green": "#00b140"}[background]
            preview = Image.new("RGBA", result.size, colour)
            preview.alpha_composite(result)
        st.image(preview, use_container_width=True)

        stem = uploaded.name.rsplit(".", 1)[0]
        st.download_button(
            "⬇️ Download PNG (transparent)",
            result_bytes,
            file_name=f"{stem}_no_bg.png",
            mime="image/png",
            use_container_width=True,
        )
