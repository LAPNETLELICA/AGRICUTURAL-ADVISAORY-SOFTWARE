from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.exceptions import KnowledgeValidationError
from engine.models.enums import TreeId
from integrations.knowledge import JSONKnowledgeProvider


def test_demo_knowledge_loads_with_development_statuses(container):
    metadata = container.knowledge.metadata()
    assert metadata["crop_count"] == 1
    assert metadata["rule_count"] == 5
    assert metadata["production_ready"] is False


def test_production_status_filter_excludes_demo_drafts():
    project_root = Path(__file__).resolve().parents[2]
    provider = JSONKnowledgeProvider(project_root / "knowledge", {"validated"})
    assert provider.list_crop_profiles() == []
    assert provider.metadata()["rule_count"] == 0


def test_rules_are_filtered_by_crop_and_tree(container, context):
    rules = container.knowledge.get_relevant_rules(
        "irish-potato", context, [TreeId.CROP_PROFILE, TreeId.SOIL]
    )
    assert [rule.domain for rule in rules] == [TreeId.CROP_PROFILE, TreeId.SOIL]


def test_duplicate_rule_id_is_rejected(tmp_path: Path):
    (tmp_path / "crops").mkdir()
    (tmp_path / "rules").mkdir()
    crop = {
        "crop_id": "test-crop",
        "name": "Test",
        "family": "Testaceae",
        "cycle_length_days": 80,
        "version": "1",
        "status": "test_only",
        "source": {"title": "Test"},
    }
    (tmp_path / "crops" / "crop.json").write_text(json.dumps(crop), encoding="utf-8")
    candidate = {
        "candidate_id": "candidate-1",
        "type": "advisory",
        "name": "test",
        "summary": "test",
    }
    rule = {
        "rule_id": "duplicate-rule",
        "crop_id": "test-crop",
        "domain": "T1",
        "version": "1",
        "status": "test_only",
        "source": {"title": "Test"},
        "candidate": candidate,
    }
    second = {**rule, "candidate": {**candidate, "candidate_id": "candidate-2"}}
    (tmp_path / "rules" / "rules.json").write_text(
        json.dumps([rule, second]), encoding="utf-8"
    )
    with pytest.raises(KnowledgeValidationError, match="duplicate rule_id"):
        JSONKnowledgeProvider(tmp_path, {"test_only"})


def test_missing_knowledge_path_is_rejected(tmp_path: Path):
    with pytest.raises(KnowledgeValidationError, match="does not exist"):
        JSONKnowledgeProvider(tmp_path / "missing", {"validated"})


def test_domain_rule_in_wrong_section_14_folder_is_rejected(tmp_path: Path):
    (tmp_path / "crops").mkdir()
    (tmp_path / "soils").mkdir()
    crop = {
        "crop_id": "test-crop",
        "name": "Test",
        "family": "Testaceae",
        "cycle_length_days": 80,
        "version": "1",
        "status": "test_only",
        "source": {"title": "Test"},
    }
    rule = {
        "rule_id": "misplaced-rule",
        "crop_id": "test-crop",
        "domain": "T5",
        "version": "1",
        "status": "test_only",
        "source": {"title": "Test"},
        "candidate": {
            "candidate_id": "misplaced-candidate",
            "type": "advisory",
            "name": "test",
            "summary": "test",
        },
    }
    (tmp_path / "crops" / "crop.json").write_text(json.dumps(crop), encoding="utf-8")
    (tmp_path / "soils" / "wrong-domain.json").write_text(
        json.dumps([rule]), encoding="utf-8"
    )
    with pytest.raises(KnowledgeValidationError, match="soils requires domain T2"):
        JSONKnowledgeProvider(tmp_path, {"test_only"})
