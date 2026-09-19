"""Tests for settings resolution and the LLM client (against a fake server)."""

from __future__ import annotations

import pytest

from ai_alchemy.config import PROVIDERS, resolve_settings
from ai_alchemy.llm import LLMClient, LLMError, parse_json_response, strip_code_fences

# ---------------------------------------------------------------- settings


def test_resolve_settings_defaults_to_openai_when_empty():
    settings = resolve_settings(env={})
    assert settings.provider is PROVIDERS["openai"]
    assert settings.model == "gpt-4o-mini"
    assert not settings.is_configured


def test_resolve_settings_priority_session_over_secrets_over_env():
    settings = resolve_settings(
        overrides={"LLM_MODEL": "from-session"},
        secrets={"LLM_MODEL": "from-secrets", "LLM_API_KEY": "secret-key"},
        env={"LLM_MODEL": "from-env", "LLM_API_KEY": "env-key", "LLM_PROVIDER": "groq"},
    )
    assert settings.model == "from-session"
    assert settings.api_key == "secret-key"
    assert settings.provider is PROVIDERS["groq"]
    assert settings.base_url == PROVIDERS["groq"].base_url
    assert settings.is_configured


def test_resolve_settings_blank_override_falls_through():
    settings = resolve_settings(overrides={"LLM_API_KEY": "   "}, env={"OPENAI_API_KEY": "sk-env"})
    assert settings.api_key == "sk-env"


def test_ollama_needs_no_key_and_custom_needs_base_url():
    assert resolve_settings(env={"LLM_PROVIDER": "ollama"}).is_configured
    custom = resolve_settings(env={"LLM_PROVIDER": "custom", "LLM_MODEL": "m", "LLM_API_KEY": "k"})
    assert not custom.is_configured
    custom = resolve_settings(
        env={
            "LLM_PROVIDER": "custom",
            "LLM_MODEL": "m",
            "LLM_API_KEY": "k",
            "LLM_BASE_URL": "http://x/v1",
        }
    )
    assert custom.is_configured


def test_unknown_provider_maps_to_custom():
    assert resolve_settings(env={"LLM_PROVIDER": "nope"}).provider is PROVIDERS["custom"]


# ------------------------------------------------------------ json parsing


@pytest.mark.parametrize(
    "raw",
    [
        '{"a": 1}',
        '```json\n{"a": 1}\n```',
        'Sure! Here is the JSON:\n{"a": 1}\nHope that helps.',
        '{"a": 1,}',
        '```\n{"a": 1, "b": [1, 2,],}\n```',
    ],
)
def test_parse_json_response_tolerates_common_wrapping(raw):
    assert parse_json_response(raw)["a"] == 1


def test_parse_json_response_rejects_garbage():
    with pytest.raises(LLMError):
        parse_json_response("no json here")
    with pytest.raises(LLMError):
        parse_json_response("[1, 2, 3]")  # a list is not an object


def test_strip_code_fences():
    assert strip_code_fences("```latex\nx^2\n```") == "x^2"
    assert strip_code_fences("plain") == "plain"
    assert strip_code_fences("```\nmulti\nline\n```") == "multi\nline"


# ---------------------------------------------------------------- client


def _client(fake_server) -> LLMClient:
    settings = resolve_settings(
        env={
            "LLM_PROVIDER": "custom",
            "LLM_BASE_URL": fake_server.base_url,
            "LLM_MODEL": "fake-model",
            "LLM_API_KEY": "k",
        }
    )
    return LLMClient(settings)


def test_complete_sends_system_and_user(fake_server):
    fake_server.reply = "hello there"
    assert _client(fake_server).complete("SYS", "USR") == "hello there"
    body = fake_server.requests[-1]
    assert body["model"] == "fake-model"
    assert body["messages"] == [
        {"role": "system", "content": "SYS"},
        {"role": "user", "content": "USR"},
    ]


def test_stream_yields_chunks_that_join_to_full_text(fake_server):
    fake_server.reply = "streaming works fine"
    chunks = list(_client(fake_server).complete_stream("s", "u"))
    assert len(chunks) > 1
    assert "".join(chunks) == "streaming works fine"
    assert fake_server.requests[-1]["stream"] is True


def test_complete_json_retries_once_then_parses(fake_server):
    replies = iter(["not json", '```json\n{"band": 6.5}\n```'])
    fake_server.reply = lambda _body: next(replies)
    assert _client(fake_server).complete_json("s", "u") == {"band": 6.5}
    assert len(fake_server.requests) == 2


def test_describe_image_sends_data_url(fake_server):
    fake_server.reply = "x^2"
    assert _client(fake_server).describe_image("read", b"\x89PNG", "image/png") == "x^2"
    content = fake_server.requests[-1]["messages"][1]["content"]
    assert content[0] == {"type": "text", "text": "read"}
    assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")


def test_http_errors_become_friendly_llm_errors(fake_server):
    fake_server.status = 401
    with pytest.raises(LLMError, match="rejected the API key"):
        _client(fake_server).ping()


def test_connection_error_is_friendly():
    settings = resolve_settings(
        env={
            "LLM_PROVIDER": "custom",
            "LLM_BASE_URL": "http://127.0.0.1:9/v1",
            "LLM_MODEL": "m",
            "LLM_API_KEY": "k",
        }
    )
    with pytest.raises(LLMError, match="Could not reach"):
        LLMClient(settings, max_retries=0).ping()
