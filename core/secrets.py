"""Secrets access, behind an interface so the backing store can be swapped.

The demo backs this with plain environment variables (EnvSecretsProvider).
A real deployment would back it with a real secrets manager -- see the
CloudSecretsProvider stub below for the swap point.
"""
import os
from abc import ABC, abstractmethod


class SecretsProvider(ABC):
    @abstractmethod
    def get(self, key: str) -> str | None:
        ...


class EnvSecretsProvider(SecretsProvider):
    """Reads secrets from process environment variables (via python-dotenv's .env loading)."""

    def get(self, key: str) -> str | None:
        return os.getenv(key)


class CloudSecretsProvider(SecretsProvider):
    """Stub for a real secrets backend (e.g. AWS Secrets Manager, HashiCorp Vault).

    Not implemented -- this repo has no cloud infrastructure to back it with.
    A real implementation would authenticate to the secrets backend in __init__
    and fetch/cache values in get().
    """

    def get(self, key: str) -> str | None:
        raise NotImplementedError(
            "CloudSecretsProvider is a stub. Implement get() against your "
            "secrets backend (e.g. boto3 secretsmanager, hvac) to use it."
        )


_PROVIDERS: dict[str, type[SecretsProvider]] = {
    "env": EnvSecretsProvider,
    "cloud": CloudSecretsProvider,
}


def secrets_provider() -> SecretsProvider:
    name = os.getenv("SECRETS_PROVIDER", "env").lower()
    if name not in _PROVIDERS:
        raise ValueError(f"Unknown SECRETS_PROVIDER '{name}'. Available: {list(_PROVIDERS)}")
    return _PROVIDERS[name]()
