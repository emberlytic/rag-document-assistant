import pytest

import core.generator as generator
from core.resilience import get_breaker


def test_available_providers_includes_only_ollama_when_no_keys_set(monkeypatch):
    for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY"):
        monkeypatch.delenv(key, raising=False)

    ids = [p["id"] for p in generator.available_providers()]
    assert ids == ["ollama"]


def test_available_providers_includes_configured_keys(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    ids = [p["id"] for p in generator.available_providers()]
    assert "claude" in ids
    assert "ollama" in ids
    assert "openai" not in ids


def test_build_user_message_includes_citation_metadata():
    chunks = [{"source": "a.pdf", "page": 3, "version": 2, "text": "some text"}]
    msg = generator._build_user_message("What happened?", chunks, "")
    assert "Source: a.pdf" in msg
    assert "Page 3" in msg
    assert "Version 2" in msg
    assert "What happened?" in msg


def test_dispatch_defaults_to_claude(monkeypatch):
    monkeypatch.delenv("LLM_BACKEND", raising=False)
    monkeypatch.setattr(
        generator, "_claude", lambda msg: generator.GenerationResult("answer", "claude", "m")
    )

    result = generator._dispatch("q", [], "", "")
    assert result.provider == "claude"


def test_dispatch_routes_to_explicit_provider(monkeypatch):
    monkeypatch.setattr(
        generator, "_openai", lambda msg: generator.GenerationResult("answer", "openai", "m")
    )

    result = generator._dispatch("q", [], "", "openai")
    assert result.provider == "openai"


def test_dispatch_falls_back_to_next_provider_on_failure(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    def failing_claude(msg):
        raise RuntimeError("claude is down")

    monkeypatch.setattr(generator, "_claude", failing_claude)
    monkeypatch.setattr(
        generator, "_openai", lambda msg: generator.GenerationResult("answer", "openai", "m")
    )

    result = generator._dispatch("q", [], "", "claude")
    assert result.provider == "openai"
    assert result.attempts == ["claude:error", "openai:ok"]


def test_dispatch_raises_when_all_providers_fail(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    def failing_ollama(msg):
        raise RuntimeError("ollama is down")

    monkeypatch.setattr(generator, "_ollama", failing_ollama)

    with pytest.raises(RuntimeError, match="All providers failed"):
        generator._dispatch("q", [], "", "ollama")


def test_dispatch_skips_provider_with_open_breaker(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    breaker = get_breaker("claude")
    breaker.failure_threshold = 1
    breaker.record_failure()  # opens the breaker
    assert breaker.state == "open"

    claude_called = False

    def should_not_be_called(msg):
        nonlocal claude_called
        claude_called = True
        return generator.GenerationResult("answer", "claude", "m")

    monkeypatch.setattr(generator, "_claude", should_not_be_called)
    monkeypatch.setattr(
        generator, "_ollama", lambda msg: generator.GenerationResult("answer", "ollama", "m")
    )

    result = generator._dispatch("q", [], "", "claude")
    assert claude_called is False
    assert result.provider == "ollama"
    assert result.attempts[0] == "claude:breaker_open"
