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


def test_visitor_key_beats_host_key_and_unlocks_model_choice():
    settings = resolve_settings(
        overrides={"LLM_API_KEY": "visitor-key", "LLM_MODEL": "from-session"},
        secrets={"LLM_PROVIDER": "groq", "LLM_API_KEY": "host-key", "LLM_MODEL": "host-model"},
        env={"LLM_API_KEY": "env-key"},
    )
    assert settings.provider is PROVIDERS["groq"]
    assert settings.api_key == "visitor-key"
    assert settings.key_source == "session"
    assert settings.model == "from-session"
    assert not settings.is_shared


def test_host_key_gives_shared_mode_with_locked_model():
    settings = resolve_settings(
        overrides={"LLM_MODEL": "gpt-4o"},  # a visitor trying to switch models
        secrets={"LLM_PROVIDER": "gemini", "LLM_API_KEY": "host-key", "DEMO_SESSION_LIMIT": "5"},
        env={},
    )
    assert settings.is_shared
    assert settings.key_source == "host"
    assert settings.model == PROVIDERS["gemini"].default_model
    assert settings.base_url == PROVIDERS["gemini"].base_url
    assert settings.demo_limit("DEMO_SESSION_LIMIT") == 5
    assert settings.demo_limit("DEMO_RPM") == 12  # default


def test_host_key_is_not_used_for_a_different_provider():
    settings = resolve_settings(
        overrides={"LLM_PROVIDER": "openai"},
        secrets={"LLM_PROVIDER": "gemini", "LLM_API_KEY": "host-key"},
        env={},
    )
    assert settings.api_key == ""
    assert settings.key_source == "none"
    assert not settings.is_configured


def test_secrets_beat_env_for_host_settings():
    settings = resolve_settings(
        secrets={"LLM_MODEL": "from-secrets", "LLM_API_KEY": "secret-key"},
        env={"LLM_MODEL": "from-env", "LLM_API_KEY": "env-key"},
    )
    assert settings.model == "from-secrets"
    assert settings.api_key == "secret-key"


def test_resolve_settings_blank_override_falls_through():
    settings = resolve_settings(overrides={"LLM_API_KEY": "   "}, env={"OPENAI_API_KEY": "sk-env"})
    assert settings.api_key == "sk-env"
    assert settings.is_shared


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


def test_before_request_hook_can_block_calls(fake_server):
    calls: list[int] = []

    def hook(messages):
        calls.append(len(messages))
        if len(calls) > 1:
            raise LLMError("blocked")

    settings = resolve_settings(
        env={
            "LLM_PROVIDER": "custom",
            "LLM_BASE_URL": fake_server.base_url,
            "LLM_MODEL": "fake-model",
            "LLM_API_KEY": "k",
        }
    )
    client = LLMClient(settings, before_request=hook)
    assert client.complete("s", "u") == "pong"
    with pytest.raises(LLMError, match="blocked"):
        list(client.complete_stream("s", "u"))
    assert len(fake_server.requests) == 1  # second call never reached the server
