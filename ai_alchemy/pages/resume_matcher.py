"""Score a resume against a job description, then generate application material."""

from __future__ import annotations

import re
from typing import Any

import streamlit as st

from ai_alchemy.llm import LLMClient
from ai_alchemy.tools.diff import diff_markdown
from ai_alchemy.tools.documents import extract_text
from ai_alchemy.ui import example_button, page_header, require_client, show_error, stream_to_ui

JOB_INFO_PROMPT = """Extract metadata from a job posting. Return JSON with exactly these keys:
{"company": string or "unknown", "title": string or "unknown", "location": string or "unknown",
 "seniority": one of "intern" | "junior" | "mid" | "senior" | "lead" | "unknown"}"""

MATCH_PROMPT = """You are an experienced technical recruiter and resume coach.
Compare the resume to the job description and return JSON with exactly these keys:
{
  "match_score": integer 0-100 (overall fit, weighing required skills and experience most),
  "verdict": one sentence explaining the score,
  "strengths": [3-5 short bullets where the candidate clearly fits],
  "gaps": [3-5 short bullets: requirements the resume does not evidence],
  "keywords": {"present": [job keywords found in the resume], "missing": [important job keywords absent from the resume]},
  "revised_summary": a 3-4 sentence professional summary rewritten to target this job, using only facts from the resume,
  "phrases_to_adjust": [{"original": exact phrase from the resume, "improved": stronger, job-aligned rewrite}] (3 items),
  "skills_to_add": [up to 5 skills the candidate likely has but should surface, or should acquire],
  "skills_to_remove": [up to 3 resume items irrelevant to this job]
}
Be honest: do not inflate the score and never invent experience."""

COVER_LETTER_PROMPT = """You write concise, specific cover letters (max 300 words, 4 paragraphs).
Use only facts from the resume. Mirror the job's language, open with a hook tied to the company
or role, quantify achievements where the resume does, and end with a confident, brief close.
Address it to the hiring manager. Output the letter only."""

INTERVIEW_PROMPT = """You are an interview coach. Based on the resume and job description, produce:
1. **Likely questions** - 6 questions (mix of technical, behavioural and gap-probing), each with
   a 2-3 sentence model answer written in the candidate's voice using their actual experience.
2. **Questions to ask the interviewer** - 3 sharp, role-specific questions.
Use Markdown headings and keep it skimmable."""

SAMPLE_JOB = """Senior Data Scientist - Acme Analytics (Remote, EU)

We're looking for a Senior Data Scientist to own forecasting and experimentation for our
marketplace. You'll build models in Python (pandas, scikit-learn, PyTorch), ship them with
MLOps tooling (MLflow, Docker, Airflow), design A/B tests, and communicate results to product
leadership. Requirements: 5+ years in data science, strong SQL, experience with time-series
forecasting and causal inference, and production ML experience on AWS or GCP. Nice to have:
LLM application experience, Streamlit or dashboarding, and mentoring junior scientists."""


def _pair(resume: str, job: str) -> str:
    return f"<resume>\n{resume}\n</resume>\n\n<job_description>\n{job}\n</job_description>"


def _score_int(value: Any) -> int:
    match = re.search(r"\d+", str(value))
    return max(0, min(100, int(match.group()))) if match else 0


def _show_match(result: dict[str, Any]) -> None:
    score = _score_int(result.get("match_score"))
    colour = "green" if score >= 75 else "orange" if score >= 50 else "red"

    score_col, verdict_col = st.columns([1, 3])
    score_col.metric("Match score", f"{score}%")
    score_col.progress(score / 100)
    verdict_col.markdown(f"**:{colour}[{result.get('verdict', '')}]**")

    strengths_col, gaps_col = st.columns(2)
    with strengths_col, st.container(border=True):
        st.markdown("#### ✅ Strengths")
        for item in result.get("strengths", []):
            st.markdown(f"- {item}")
    with gaps_col, st.container(border=True):
        st.markdown("#### ⚠️ Gaps")
        for item in result.get("gaps", []):
            st.markdown(f"- {item}")

    keywords = result.get("keywords", {}) or {}
    st.markdown("#### 🔑 Keyword coverage")
    present, missing = keywords.get("present", []), keywords.get("missing", [])
    st.markdown(
        " ".join(f":green-badge[{kw}]" for kw in present)
        + " "
        + " ".join(f":red-badge[{kw}]" for kw in missing)
        or "_none detected_"
    )

    st.markdown("#### ✏️ Revised professional summary")
    st.code(result.get("revised_summary", ""), language=None, wrap_lines=True)

    st.markdown("#### 🔄 Phrases to strengthen")
    for item in result.get("phrases_to_adjust", []):
        if isinstance(item, dict):
            st.markdown(
                diff_markdown(str(item.get("original", "")), str(item.get("improved", ""))),
                unsafe_allow_html=True,
            )
            st.markdown("")

    add_col, remove_col = st.columns(2)
    with add_col:
        st.markdown("#### 🌱 Skills to add or surface")
        for skill in result.get("skills_to_add", []):
            st.markdown(f"- :green[{skill}]")
    with remove_col:
        st.markdown("#### 🗑️ Consider removing")
        for skill in result.get("skills_to_remove", []):
            st.markdown(f"- :red[{skill}]")


def render() -> None:
    page_header(
        "Resume Matcher",
        "📄",
        "Honest fit analysis plus a tailored cover letter and interview prep.",
    )
    client: LLMClient = require_client()

    resume_col, job_col = st.columns(2)
    with resume_col:
        st.markdown("##### Resume")
        uploaded = st.file_uploader(
            "PDF, DOCX or TXT", type=["pdf", "docx", "txt", "md"], label_visibility="collapsed"
        )
        resume_text = ""
        if uploaded is not None:
            try:
                resume_text = extract_text(uploaded.name, uploaded.getvalue())
            except Exception as exc:  # noqa: BLE001
                show_error(exc)
        resume_text = st.text_area(
            "Or paste it",
            value=resume_text,
            height=260,
            placeholder="Paste resume text...",
            key="rm_resume",
        )
    with job_col:
        st.markdown("##### Job description")
        job_text = st.text_area(
            "Job description",
            height=300,
            key="rm_job",
            label_visibility="collapsed",
            placeholder="Paste the job posting...",
        )
        example_button("Load a sample job posting", "rm_job", SAMPLE_JOB)

    options = st.multiselect(
        "What to generate",
        ["Match analysis", "Cover letter", "Interview prep"],
        default=["Match analysis"],
    )
    run = st.button("🚀 Run", type="primary", use_container_width=True, disabled=not options)
    if not run:
        return
    if not resume_text.strip() or not job_text.strip():
        st.warning("Both a resume and a job description are needed.")
        return

    pair = _pair(resume_text, job_text)
    try:
        with st.spinner("Reading the job posting..."):
            job_info = client.complete_json(JOB_INFO_PROMPT, job_text, temperature=0)
    except Exception as exc:  # noqa: BLE001
        show_error(exc)
        return

    st.markdown(
        f"💼 **{job_info.get('title', 'unknown')}** at **{job_info.get('company', 'unknown')}** · "
        f"📍 {job_info.get('location', 'unknown')} · 🎚️ {job_info.get('seniority', 'unknown')}"
    )
    slug = re.sub(
        r"[^A-Za-z0-9]+", "_", f"{job_info.get('company', 'job')}_{job_info.get('title', '')}"
    ).strip("_")

    tabs = st.tabs(options)
    for tab, option in zip(tabs, options, strict=True):
        with tab:
            if option == "Match analysis":
                try:
                    with st.spinner("Scoring the match..."):
                        result = client.complete_json(MATCH_PROMPT, pair, temperature=0)
                    _show_match(result)
                except Exception as exc:  # noqa: BLE001
                    show_error(exc)
            elif option == "Cover letter":
                letter = stream_to_ui(
                    client.complete_stream(COVER_LETTER_PROMPT, pair, temperature=0.5)
                )
                if letter:
                    st.download_button(
                        "⬇️ Download cover letter",
                        letter,
                        file_name=f"cover_letter_{slug}.md",
                        mime="text/markdown",
                    )
            elif option == "Interview prep":
                prep = stream_to_ui(client.complete_stream(INTERVIEW_PROMPT, pair, temperature=0.5))
                if prep:
                    st.download_button(
                        "⬇️ Download interview prep",
                        prep,
                        file_name=f"interview_prep_{slug}.md",
                        mime="text/markdown",
                    )
