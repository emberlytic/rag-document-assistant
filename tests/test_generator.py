import core.generator as generator


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
