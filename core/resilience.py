"""Per-provider circuit breaker for LLM generation calls.

In-process and non-persistent -- state resets on restart, and each worker
process tracks its own breakers. That's the right scope for a single-instance
demo; a multi-worker production deployment would back this with shared state
(e.g. Redis) instead.
"""
import time
from dataclasses import dataclass, field

CLOSED = "closed"
OPEN = "open"
HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    failure_threshold: int = 3
    cooldown_seconds: float = 30.0
    _failure_count: int = field(default=0, init=False)
    _state: str = field(default=CLOSED, init=False)
    _opened_at: float = field(default=0.0, init=False)

    @property
    def state(self) -> str:
        if self._state == OPEN and (time.monotonic() - self._opened_at) >= self.cooldown_seconds:
            self._state = HALF_OPEN
        return self._state

    def allow_request(self) -> bool:
        return self.state != OPEN

    def record_success(self) -> None:
        self._failure_count = 0
        self._state = CLOSED

    def record_failure(self) -> None:
        self._failure_count += 1
        if self.state == HALF_OPEN or self._failure_count >= self.failure_threshold:
            self._state = OPEN
            self._opened_at = time.monotonic()


_breakers: dict[str, CircuitBreaker] = {}


def get_breaker(provider_id: str) -> CircuitBreaker:
    if provider_id not in _breakers:
        _breakers[provider_id] = CircuitBreaker()
    return _breakers[provider_id]


def breaker_states() -> dict[str, str]:
    return {provider_id: b.state for provider_id, b in _breakers.items()}
