"""Central registry of all demo configs — import from here."""
from demos.medical import config as medical
from demos.legal import config as legal
from demos.tech_support import config as tech_support

ALL_DEMOS: dict = {
    "medical": medical,
    "legal": legal,
    "tech_support": tech_support,
}


def get_demo(name: str):
    if name not in ALL_DEMOS:
        raise ValueError(f"Unknown demo '{name}'. Available: {list(ALL_DEMOS)}")
    return ALL_DEMOS[name]
