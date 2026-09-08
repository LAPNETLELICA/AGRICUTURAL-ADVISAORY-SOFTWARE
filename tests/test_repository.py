from backend2.repository import KnowledgeRepository


def test_tomato_profile_exists():
    repo = KnowledgeRepository()
    profile = repo.get_crop_profile("tomato")
    assert profile is not None
    assert profile.crop_id == "tomato"
    assert profile.name == "Tomate"
    assert profile.family == "Solanaceae"
    assert profile.cycle_days == 125
    assert profile.cycle_length_days == 125
    assert "pepiniere" in profile.growth_stages
    assert "recolte" in profile.growth_stages
    assert profile.tolerances.get("optimal_temperature_c") == [20, 24]
    assert profile.tolerances.get("optimal_ph") == [5.5, 7.0]


def test_tomato_rules_are_crop_scoped():
    repo = KnowledgeRepository()
    rules = repo.get_relevant_rule_definitions("tomato", ["soil", "weather", "timing"])
    assert rules
    assert all(rule.crop_id == "tomato" for rule in rules)


def test_tomato_rules_coverage():
    repo = KnowledgeRepository()
    expected_trees = {"profile", "soil", "region", "topography", "weather", "timing", "practices_risks"}
    rules = [r for r in repo.get_rules() if r.crop_id == "tomato"]
    assert len(rules) >= 7
    found_trees = {r.tree for r in rules}
    assert expected_trees.issubset(found_trees)


def test_only_tomato_in_repository():
    repo = KnowledgeRepository()
    crops = repo.get_crop_ids()
    assert crops == ["tomato"]
