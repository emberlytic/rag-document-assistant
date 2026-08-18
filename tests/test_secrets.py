import pytest

from core.secrets import EnvSecretsProvider, CloudSecretsProvider, secrets_provider


def test_env_secrets_provider_reads_from_environment(monkeypatch):
    monkeypatch.setenv("SOME_KEY", "some-value")
    assert EnvSecretsProvider().get("SOME_KEY") == "some-value"


def test_env_secrets_provider_returns_none_for_missing_key(monkeypatch):
    monkeypatch.delenv("MISSING_KEY", raising=False)
    assert EnvSecretsProvider().get("MISSING_KEY") is None


def test_secrets_provider_defaults_to_env(monkeypatch):
    monkeypatch.delenv("SECRETS_PROVIDER", raising=False)
    assert isinstance(secrets_provider(), EnvSecretsProvider)


def test_secrets_provider_selects_cloud_provider(monkeypatch):
    monkeypatch.setenv("SECRETS_PROVIDER", "cloud")
    assert isinstance(secrets_provider(), CloudSecretsProvider)


def test_cloud_secrets_provider_is_unimplemented_stub():
    with pytest.raises(NotImplementedError):
        CloudSecretsProvider().get("ANYTHING")


def test_secrets_provider_rejects_unknown_backend(monkeypatch):
    monkeypatch.setenv("SECRETS_PROVIDER", "nonsense")
    with pytest.raises(ValueError):
        secrets_provider()
