from pathlib import Path

from engine.models.enums import TreeId
from integrations.cameroon_knowledge import CameroonKnowledgeProvider


def _provider() -> CameroonKnowledgeProvider:
    return CameroonKnowledgeProvider(Path("BASE_CONNAISSANCES_AGRICOLES"))


def test_provider_lists_crops():
    crops = [profile.crop_id for profile in _provider().list_crop_profiles()]
    assert "potato" in crops


def test_provider_gets_crop_profile():
    profile = _provider().get_crop_profile("potato")
    assert profile is not None
    assert profile.crop_id == "potato"
    assert profile.family == "FAM_TUBERCULES_RACINES"


def test_provider_filters_rules_by_tree():
    rules = _provider().get_relevant_rules(
        crop_id="potato", context=None, trees=[TreeId.WEATHER, TreeId.TIMING]
    )
    assert [rule.domain for rule in rules] == [TreeId.WEATHER, TreeId.TIMING]


def test_provider_lists_tomato():
    crops = [profile.crop_id for profile in _provider().list_crop_profiles()]
    assert "tomato" in crops


def test_provider_gets_tomato_profile():
    profile = _provider().get_crop_profile("tomato")
    assert profile is not None
    assert profile.crop_id == "tomato"
    assert profile.name == "Tomate"
    assert profile.cycle_length_days == 125


def test_provider_tomato_tree_filtering():
    rules = _provider().get_relevant_rules(
        crop_id="tomato",
        context=None,
        trees=[TreeId.WEATHER, TreeId.TIMING, TreeId.PRACTICES_RISKS],
    )
    assert len(rules) >= 3
    assert all(r.crop_id == "tomato" for r in rules)
    assert {rule.domain for rule in rules} == {
        TreeId.WEATHER,
        TreeId.TIMING,
        TreeId.PRACTICES_RISKS,
    }
