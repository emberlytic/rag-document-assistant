import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


@pytest.fixture(autouse=True)
def _reset_circuit_breakers():
    """Provider circuit breakers are process-global state; keep tests isolated."""
    import core.resilience as resilience
    resilience._breakers.clear()
    yield
    resilience._breakers.clear()
