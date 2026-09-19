"""IELTS writing assessment with per-criterion band scores."""

from __future__ import annotations

from typing import Any

import streamlit as st

from ai_alchemy.tools.diff import diff_markdown
from ai_alchemy.ui import example_button, page_header, require_client, show_error, word_count

CRITERIA = {
    "task_response": "Task Response",
    "coherence_cohesion": "Coherence & Cohesion",
    "lexical_resource": "Lexical Resource",
    "grammar": "Grammatical Range & Accuracy",
}

EXAMINER_PROMPT = """You are a certified IELTS writing examiner applying the official public band
descriptors strictly. Assess the essay for {task} and return JSON with exactly these keys:
{{
  "overall_band": number (0-9, in 0.5 steps, the average of the four criteria rounded to the nearest 0.5),
  "criteria": {{
    "task_response": {{"band": number, "comment": one or two sentences}},
    "coherence_cohesion": {{"band": number, "comment": one or two sentences}},
    "lexical_resource": {{"band": number, "comment": one or two sentences}},
    "grammar": {{"band": number, "comment": one or two sentences}}
  }},
  "feedback": a paragraph (max 120 words) of the most important advice to reach the next band,
  "mistakes": [{{"original": exact sentence from the essay, "correction": corrected sentence, "explanation": short reason}}] (up to 8, most impactful first),
  "improved_vocabulary": [{{"original": word or phrase used, "suggestion": more precise or academic alternative}}] (up to 5)
}}
Be calibrated: a typical intermediate learner scores 5.5-6.5. Do not be generous."""

OCR_PROMPT = """Transcribe the handwritten or typed English text in this image exactly, preserving
paragraph breaks. Output only the transcription with no commentary."""

SAMPLE_ESSAY = """Some people believe that universities should focus on providing academic skills, while others think they should prepare students for employment. Discuss both views and give your opinion.

In today's competitive world, the purpose of university education is a topic of much debate. While some argue that universities should concentrate on academic knowledge, others believe that preparing students for the job market is more important. In my opinion, both aims are essential and should be balanced.

On the one hand, academic skills are the foundation of higher education. Universities have traditionally been places where students learn to think critically, analyse complex problems and conduct research. These abilities is valuable in any career, because they allow graduates to adapt to new situation and keep learning through their lives. For example, a philosophy student may not use Plato at work, but the logical thinking they developed will help them in many fields.

On the other hand, many students attend university mainly to improve their career prospects, and they expect to gain practical skills. Employers frequently complain that graduates lack experience of real working environments. Therefore, courses which include internships, projects with companies and training in communication can make students more employable and reduce unemployment among young people.

In conclusion, although academic skills remain the core of university education, I believe institutions have a responsibility to also prepare their students for employment. A combination of both approaches would benefit students, employers and society as a whole."""


def _band_colour(band: float) -> str:
    return "green" if band >= 7 else "orange" if band >= 5.5 else "red"


def _show_result(result: dict[str, Any]) -> None:
    overall = float(result.get("overall_band", 0) or 0)
    st.markdown(f"## Overall band: :{_band_colour(overall)}[{overall:.1f}] / 9")

    criteria = result.get("criteria", {}) or {}
    cols = st.columns(4)
    for col, (key, label) in zip(cols, CRITERIA.items(), strict=True):
        entry = criteria.get(key, {}) or {}
        band = float(entry.get("band", 0) or 0)
        with col, st.container(border=True):
            st.metric(label, f"{band:.1f}")
            st.caption(entry.get("comment", ""))

    st.markdown("#### 🎯 How to reach the next band")
    st.info(result.get("feedback", ""))

    mistakes = result.get("mistakes", []) or []
    if mistakes:
        st.markdown(f"#### ✏️ Corrections ({len(mistakes)})")
        for index, item in enumerate(mistakes, start=1):
            if not isinstance(item, dict):
                continue
            with st.expander(f"{index}. {item.get('explanation', 'Correction')}"):
                st.markdown(
                    diff_markdown(str(item.get("original", "")), str(item.get("correction", ""))),
                    unsafe_allow_html=True,
                )

    vocab = result.get("improved_vocabulary", []) or []
    if vocab:
        st.markdown("#### 📚 Vocabulary upgrades")
        st.table(
            [
                {"You wrote": v.get("original", ""), "Try": v.get("suggestion", "")}
                for v in vocab
                if isinstance(v, dict)
            ]
        )


def render() -> None:
    page_header(
        "IELTS Writing Examiner",
        "🎓",
        "Calibrated band scores per criterion with highlighted corrections.",
    )
    client = require_client()

    task = st.segmented_control(
        "Task",
        ["Task 2 (essay)", "Task 1 (Academic report)", "Task 1 (General letter)"],
        default="Task 2 (essay)",
    )
    text_tab, image_tab = st.tabs(["✍️ Paste text", "📷 Upload a photo"])
    with text_tab:
        essay = st.text_area(
            "Your writing", height=320, key="ielts_text", placeholder="Paste your essay here..."
        )
        example_button("Load a sample essay", "ielts_text", SAMPLE_ESSAY)
        if essay:
            st.caption(f"{word_count(essay)} words")
    with image_tab:
        image = st.file_uploader(
            "Photo of handwritten or typed text", type=["png", "jpg", "jpeg", "webp"]
        )
        st.caption("Requires a vision-capable model (e.g. gpt-4o-mini, gemini-2.0-flash, llava).")

    if not st.button("🚀 Evaluate", type="primary", use_container_width=True):
        return

    if image is not None:
        try:
            with st.spinner("Reading the image..."):
                essay = client.describe_image(
                    OCR_PROMPT, image.getvalue(), image.type or "image/png", temperature=0
                )
            with st.expander("Transcribed text", expanded=False):
                st.write(essay)
        except Exception as exc:  # noqa: BLE001
            show_error(exc)
            return

    if not essay or not essay.strip():
        st.warning("Paste your writing or upload a photo first.")
        return
    if word_count(essay) < 50:
        st.warning(
            "That is very short - IELTS responses are usually 150-350 words. Assessing anyway."
        )

    try:
        with st.spinner("Examining..."):
            result = client.complete_json(EXAMINER_PROMPT.format(task=task), essay, temperature=0)
        _show_result(result)
    except Exception as exc:  # noqa: BLE001
        show_error(exc)
