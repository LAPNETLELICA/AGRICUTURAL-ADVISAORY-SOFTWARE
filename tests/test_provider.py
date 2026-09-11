import pytest

from backend2.provider import KnowledgeProvider


def test_provider_lists_crops():
    provider = KnowledgeProvider()
    crops = provider.list_crops()
    assert "potato" in crops


def test_provider_gets_crop_profile():
    provider = KnowledgeProvider()
    profile = provider.get_crop_profile("potato")
    assert profile is not None
    assert profile.crop_id == "potato"
    assert profile.family == "Solanaceae"


def test_provider_rule_definitions_filtering():
    provider = KnowledgeProvider()
    rules = provider.get_relevant_rule_definitions(
        crop_id="potato", context={"test": True}, trees=["weather", "timing"]
    )
    assert len(rules) >= 2
    assert all(r.tree in ["weather", "timing"] for r in rules)


def test_provider_get_relevant_rules_raises_explicit_error_without_backend1():
    provider = KnowledgeProvider()
    with pytest.raises(RuntimeError) as exc_info:
        provider.get_relevant_rules("potato", context=None, trees=["weather"])
    assert "Backend 1 contracts are missing" in str(exc_info.value)


def test_provider_lists_tomato():
    provider = KnowledgeProvider()
    crops = provider.list_crops()
    assert "tomato" in crops


def test_provider_gets_tomato_profile():
    provider = KnowledgeProvider()
    profile = provider.get_crop_profile("tomato")
    assert profile is not None
    assert profile.crop_id == "tomato"
    assert profile.name == "Tomate"
    assert profile.cycle_days == 125


def test_provider_tomato_tree_filtering():
    provider = KnowledgeProvider()
    rules = provider.get_relevant_rule_definitions(
        crop_id="tomato", context={"test": True}, trees=["weather", "timing", "practices_risks"]
    )
    assert len(rules) >= 3
    assert all(r.crop_id == "tomato" for r in rules)
    assert all(r.tree in ["weather", "timing", "practices_risks"] for r in rules)
