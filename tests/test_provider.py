import pytest
from knowledge.provider import KnowledgeProvider


def test_provider_lists_crops():
    provider = KnowledgeProvider()
    crops = provider.list_crops()
    assert set(crops) == {"tomato", "irish-potato"}


def test_provider_gets_irish_potato_profile():
    provider = KnowledgeProvider()
    profile = provider.get_crop_profile("irish-potato")
    assert profile is not None
    assert profile.crop_id == "irish-potato"
    assert profile.name == "Pomme de terre"
    assert profile.cycle_days == 100


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
        crop_id="tomato",
        context={"test": True},
        trees=["weather", "timing", "practices_risks"]
    )
    assert len(rules) >= 3
    assert all(r.crop_id == "tomato" for r in rules)
    assert all(r.tree in ["weather", "timing", "practices_risks"] for r in rules)


def test_provider_get_relevant_rules_integration_works():
    """Test that the canonical model integration works - returns Rule objects with CandidateTemplate."""
    try:
        from engine.models.domain import Rule
    except ImportError:
        pytest.skip("Backend 1 domain models require Pydantic v2")
    provider = KnowledgeProvider()
    rules = provider.get_relevant_rules("tomato", context=None, trees=["weather", "timing"])
    assert len(rules) >= 2
    # Verify canonical Rule structure
    for rule in rules:
        assert hasattr(rule, 'rule_id')
        assert hasattr(rule, 'candidate')
        assert hasattr(rule.candidate, 'candidate_id')
        # Should be CandidateTemplate (not Candidate with rule metadata)
        assert not hasattr(rule.candidate, 'rule_id') or rule.candidate.rule_id is None