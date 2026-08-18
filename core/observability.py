"""Structured request logging and Prometheus-format metrics.

Hand-rolled rather than pulling in prometheus_client -- the metric set here
is small and fixed, so a dependency isn't worth it at this scale.
"""
import json
import logging
import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field

from core.resilience import breaker_states

logger = logging.getLogger("rag_assistant")
logger.setLevel(logging.INFO)
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(_handler)


@dataclass
class _Metrics:
    request_count: dict[tuple[str, str, str], int] = field(default_factory=lambda: defaultdict(int))
    latency_sum_ms: dict[tuple[str, str, str], float] = field(default_factory=lambda: defaultdict(float))


_metrics = _Metrics()


@contextmanager
def track_query(demo: str):
    """Times a /query call and logs+records it. Yields a dict to fill in provider/success."""
    start = time.monotonic()
    info: dict = {"provider": "", "success": False, "attempts": []}
    try:
        yield info
    finally:
        latency_ms = (time.monotonic() - start) * 1000
        status = "success" if info["success"] else "error"
        key = (demo, info["provider"] or "unknown", status)
        _metrics.request_count[key] += 1
        _metrics.latency_sum_ms[key] += latency_ms
        logger.info(json.dumps({
            "event": "query",
            "demo": demo,
            "provider": info["provider"],
            "attempts": info["attempts"],
            "latency_ms": round(latency_ms, 1),
            "status": status,
        }))


def render_prometheus() -> str:
    lines = [
        "# HELP rag_query_requests_total Total /query requests by demo, provider, status.",
        "# TYPE rag_query_requests_total counter",
    ]
    for (demo, provider, status), count in _metrics.request_count.items():
        lines.append(
            f'rag_query_requests_total{{demo="{demo}",provider="{provider}",status="{status}"}} {count}'
        )

    lines += [
        "# HELP rag_query_latency_ms_sum Sum of /query latency in milliseconds by demo, provider, status.",
        "# TYPE rag_query_latency_ms_sum counter",
    ]
    for (demo, provider, status), total_ms in _metrics.latency_sum_ms.items():
        lines.append(
            f'rag_query_latency_ms_sum{{demo="{demo}",provider="{provider}",status="{status}"}} {total_ms:.1f}'
        )

    lines += [
        "# HELP rag_provider_circuit_breaker_state Current circuit breaker state per provider (0=closed, 1=half_open, 2=open).",
        "# TYPE rag_provider_circuit_breaker_state gauge",
    ]
    state_value = {"closed": 0, "half_open": 1, "open": 2}
    for provider, state in breaker_states().items():
        lines.append(
            f'rag_provider_circuit_breaker_state{{provider="{provider}"}} {state_value[state]}'
        )

    return "\n".join(lines) + "\n"
