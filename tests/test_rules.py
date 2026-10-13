from __future__ import annotations

from domain.models import TreeId
from repositories.rules import RuleRepository


def test_rule_repository_compiles_all_crops() -> None:
    repo = RuleRepository()
    rules = repo.list_rules()
    assert len(rules) >= 35

    crops_covered = {r.crop_id for r in rules}
    assert "CULT_TOMATE" in crops_covered
    assert "CULT_POMME_DE_TERRE" in crops_covered
    assert "CULT_MAIS" in crops_covered
    assert "CULT_HARICOT" in crops_covered
    assert "CULT_MANIOC" in crops_covered
    assert "CULT_BANANIER_PLANTAIN" in crops_covered


def test_tomato_rules_across_trees() -> None:
    repo = RuleRepository()
    tomato_rules = repo.query_rules("CULT_TOMATE")
    assert len(tomato_rules) >= 6

    trees = {r.tree for r in tomato_rules}
    assert TreeId.T1_PROFILE in trees
    assert TreeId.T2_SOIL in trees
    assert TreeId.T4_TOPOGRAPHY in trees
    assert TreeId.T5_CLIMATE in trees
    assert TreeId.T6_TIMING in trees
    assert TreeId.T7_PRACTICES in trees


def test_potato_slope_rule_actions() -> None:
    repo = RuleRepository()
    potato_topo = repo.query_rules("irish_potato", trees=[TreeId.T4_TOPOGRAPHY])
    assert len(potato_topo) == 1
    rule = potato_topo[0]
    assert rule.crop_id == "CULT_POMME_DE_TERRE"
    assert rule.candidate.type == "practice"
    assert any("courbes de niveau" in act for act in rule.candidate.actions)


def test_rule_filtering_by_trees() -> None:
    repo = RuleRepository()
    selected = repo.query_rules("CULT_MAIS", trees=["T1", "T5"])
    assert len(selected) == 2
    assert {r.tree.value for r in selected} == {"T1", "T5"}


def test_rule_has_source_reference() -> None:
    repo = RuleRepository()
    rule = repo.get_rule("RULE_CULT_TOMATE_T2_SOIL_001")
    assert rule is not None
    assert len(rule.source_refs) >= 1
    src = rule.source_refs[0]
    assert src.source_id == "DOC_MINEFOP_IFATI_TOMATE"
    assert "IFATI" in src.organization

