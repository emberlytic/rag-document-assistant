import pytest

from demos.registry import ALL_DEMOS, get_demo


def test_all_demos_registered():
    assert set(ALL_DEMOS.keys()) == {"medical", "legal", "tech_support"}


def test_get_demo_returns_matching_config():
    demo = get_demo("legal")
    assert demo.name == "Legal & HR Document Assistant"
    assert demo.collection == "legal"


def test_get_demo_raises_for_unknown_name():
    with pytest.raises(ValueError):
        get_demo("nonexistent")
