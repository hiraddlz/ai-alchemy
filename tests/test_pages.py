"""End-to-end tests: render each page with Streamlit's AppTest, driving a fake model server."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ai_alchemy.registry import TOOLS

ROOT = Path(__file__).resolve().parent.parent


def page_app(slug: str, fake_server=None, **session_state) -> AppTest:
    """Build an AppTest that renders one page module, optionally wired to the fake server."""
    script = (
        f"import sys; sys.path.insert(0, {str(ROOT).replace(chr(92), '/')!r})\n"
        "import importlib\n"
        f"importlib.import_module('ai_alchemy.pages.{slug}').render()\n"
    )
    at = AppTest.from_string(script, default_timeout=60)
    if fake_server is not None:
        at.session_state["LLM_PROVIDER"] = "custom"
        at.session_state["LLM_BASE_URL"] = fake_server.base_url
        at.session_state["LLM_MODEL"] = "fake"
        at.session_state["LLM_API_KEY"] = "k"
    for key, value in session_state.items():
        at.session_state[key] = value
    return at


def click(at: AppTest, label: str) -> AppTest:
    """Click the first button whose label contains ``label`` and rerun."""
    button = next(b for b in at.button if label in b.label)
    return button.click().run()


def test_main_app_renders_home_without_errors():
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    assert not at.exception
    assert len(at.markdown) >= len(TOOLS)  # one card per tool


@pytest.mark.parametrize("slug", [tool.slug for tool in TOOLS])
def test_every_page_renders_unconfigured(slug):
    at = page_app(slug).run()
    assert not at.exception
    assert at.title  # page header present


def test_llm_pages_prompt_for_a_key_when_unconfigured():
    at = page_app("proofreader").run()
    assert at.info and "Model settings" in at.info[0].value
    assert not at.button  # page stopped before rendering controls


def test_proofreader_end_to_end(fake_server):
    fake_server.reply = "Their are many reasons."
    at = page_app("proofreader", fake_server).run()
    at.text_area("pf_text").set_value("There are many reason.").run()
    click(at, "Proofread")

    assert not at.exception
    sent = fake_server.requests[0]
    assert sent["messages"][1]["content"] == "There are many reason."
    assert sent["stream"] is True
    markdown_text = " ".join(m.value for m in at.markdown)
    assert "line-through" in markdown_text  # diff rendered


def test_ielts_renders_structured_result(fake_server):
    fake_server.reply = json.dumps(
        {
            "overall_band": 6.5,
            "criteria": {
                "task_response": {"band": 6, "comment": "ok"},
                "coherence_cohesion": {"band": 7, "comment": "ok"},
                "lexical_resource": {"band": 6.5, "comment": "ok"},
                "grammar": {"band": 6.5, "comment": "ok"},
            },
            "feedback": "Use more complex sentences.",
            "mistakes": [
                {
                    "original": "These abilities is valuable",
                    "correction": "These abilities are valuable",
                    "explanation": "Subject-verb agreement",
                }
            ],
            "improved_vocabulary": [{"original": "good", "suggestion": "beneficial"}],
        }
    )
    at = page_app("ielts", fake_server).run()
    at.text_area("ielts_text").set_value("word " * 60).run()
    click(at, "Evaluate")

    assert not at.exception
    assert fake_server.requests[0].get("response_format") is None  # custom provider: no JSON mode
    assert [m.value for m in at.metric] == ["6.0", "7.0", "6.5", "6.5"]
    assert any("6.5" in m.value for m in at.markdown)
    assert at.expander[0].label.startswith("1. Subject-verb")


def test_resume_matcher_scores_and_streams(fake_server):
    def reply(body):
        user = body["messages"][1]["content"]
        if "<resume>" not in user:  # job-info extraction
            return json.dumps(
                {
                    "company": "Acme",
                    "title": "Data Scientist",
                    "location": "Remote",
                    "seniority": "senior",
                }
            )
        if body.get("stream"):
            return "Dear hiring manager, ..."
        return json.dumps(
            {
                "match_score": "82%",
                "verdict": "Strong fit.",
                "strengths": ["Python"],
                "gaps": ["Causal inference"],
                "keywords": {"present": ["Python"], "missing": ["Airflow"]},
                "revised_summary": "Summary.",
                "phrases_to_adjust": [{"original": "did stuff", "improved": "delivered results"}],
                "skills_to_add": ["Airflow"],
                "skills_to_remove": ["MS Paint"],
            }
        )

    fake_server.reply = reply
    at = page_app("resume_matcher", fake_server).run()
    at.text_area("rm_resume").set_value("Python developer who did stuff.").run()
    at.text_area("rm_job").set_value("Need Python and Airflow.").run()
    at.multiselect[0].set_value(["Match analysis", "Cover letter"]).run()
    click(at, "Run")

    assert not at.exception
    assert at.metric[0].value == "82%"
    text = " ".join(m.value for m in at.markdown)
    assert "Acme" in text and "Strong fit." in text and "Dear hiring manager" in text
    assert at.tabs[0].label == "Match analysis"


def test_translator_rtl_output_uses_rtl_container(fake_server):
    fake_server.reply = "سلام دنیا"
    at = page_app("translator", fake_server).run()
    at.text_area("tr_text").set_value("Hello world").run()
    at.selectbox[1].set_value("Persian").run()
    click(at, "Translate")
    assert not at.exception
    assert "into Persian" in fake_server.requests[0]["messages"][0]["content"]


def test_ascii_artist_empty_state_needs_no_model():
    # AppTest cannot drive file_uploader yet; the conversion itself is covered in test_tools.
    at = page_app("ascii_artist").run()
    assert not at.exception
    assert at.info and "Upload" in at.info[0].value


def test_error_from_model_is_shown_not_raised(fake_server):
    fake_server.status = 429
    at = page_app("summarizer", fake_server).run()
    at.text_area("sum_text").set_value("Some text to summarise.").run()
    click(at, "Summarise")
    assert not at.exception
    assert at.error and "rate limit" in at.error[0].value.lower()


def test_shared_mode_enforces_session_limit(fake_server):
    fake_server.reply = "Fixed text."
    at = page_app("proofreader")
    at.secrets["LLM_PROVIDER"] = "custom"
    at.secrets["LLM_BASE_URL"] = fake_server.base_url
    at.secrets["LLM_MODEL"] = "fake"
    at.secrets["LLM_API_KEY"] = "host-key"
    at.secrets["DEMO_SESSION_LIMIT"] = "2"
    at.secrets["DEMO_RPM"] = "1000"
    at.run()
    at.text_area("pf_text").set_value("Some text.").run()
    at.toggle[0].set_value(False).run()  # one model call per click

    click(at, "Proofread")
    click(at, "Proofread")
    assert not at.error
    assert len(fake_server.requests) == 2

    click(at, "Proofread")
    assert len(fake_server.requests) == 2  # blocked before reaching the server
    assert at.error and "free demo calls" in at.error[0].value
    assert at.session_state["demo_calls"] == 2


def test_shared_mode_rejects_oversized_prompts(fake_server):
    at = page_app("summarizer")
    at.secrets["LLM_PROVIDER"] = "custom"
    at.secrets["LLM_BASE_URL"] = fake_server.base_url
    at.secrets["LLM_MODEL"] = "fake"
    at.secrets["LLM_API_KEY"] = "host-key"
    at.secrets["DEMO_MAX_WORDS"] = "50"
    at.run()
    at.text_area("sum_text").set_value("word " * 80).run()
    click(at, "Summarise")
    assert at.error and "up to 50 words" in at.error[0].value
    assert not fake_server.requests
