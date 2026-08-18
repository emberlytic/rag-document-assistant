import time

import pytest

from core.resilience import CircuitBreaker, get_breaker, breaker_states


def test_breaker_starts_closed_and_allows_requests():
    b = CircuitBreaker()
    assert b.state == "closed"
    assert b.allow_request() is True


def test_breaker_opens_after_failure_threshold():
    b = CircuitBreaker(failure_threshold=3, cooldown_seconds=30)
    b.record_failure()
    b.record_failure()
    assert b.state == "closed"
    b.record_failure()
    assert b.state == "open"
    assert b.allow_request() is False


def test_breaker_half_opens_after_cooldown():
    b = CircuitBreaker(failure_threshold=1, cooldown_seconds=0.05)
    b.record_failure()
    assert b.state == "open"
    time.sleep(0.06)
    assert b.state == "half_open"
    assert b.allow_request() is True


def test_breaker_recovers_on_success_after_half_open():
    b = CircuitBreaker(failure_threshold=1, cooldown_seconds=0.05)
    b.record_failure()
    time.sleep(0.06)
    assert b.state == "half_open"
    b.record_success()
    assert b.state == "closed"


def test_breaker_reopens_on_failure_during_half_open():
    b = CircuitBreaker(failure_threshold=1, cooldown_seconds=0.05)
    b.record_failure()
    time.sleep(0.06)
    assert b.state == "half_open"
    b.record_failure()
    assert b.state == "open"


def test_get_breaker_returns_same_instance_per_provider():
    assert get_breaker("test-provider-a") is get_breaker("test-provider-a")


def test_breaker_states_reports_known_providers():
    get_breaker("test-provider-b")
    assert breaker_states()["test-provider-b"] == "closed"
