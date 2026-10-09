from __future__ import annotations

from pathlib import Path

import pytest

from engine.exceptions import KnowledgeValidationError
from engine.models.enums import TreeId
from integrations.cameroon_knowledge import CameroonKnowledgeProvider


def test_cameroon_knowledge_base_loads_as_the_only_provider(container):
    metadata = container.knowledge.metadata()
    assert metadata["source"] == "BASE_CONNAISSANCES_AGRICOLES"
    assert metadata["crop_count"] == 6
    assert metadata["rule_count"] == 42
    assert metadata["read_only"] is True


def test_crop_aliases_resolve_to_the_canonical_profile(container):
    profile = container.knowledge.get_crop_profile("irish-potato")
    assert profile is not None
    assert profile.crop_id == "potato"


def test_rules_are_filtered_by_crop_and_tree(container, context):
    rules = container.knowledge.get_relevant_rules(
        "irish-potato", context, [TreeId.CROP_PROFILE, TreeId.SOIL]
    )
    assert [rule.domain for rule in rules] == [TreeId.CROP_PROFILE, TreeId.SOIL]
    assert {rule.crop_id for rule in rules} == {"potato"}


def test_missing_cameroon_knowledge_path_is_rejected(tmp_path: Path):
    with pytest.raises(KnowledgeValidationError, match="not found or incomplete"):
        CameroonKnowledgeProvider(tmp_path / "missing")


def test_incomplete_cameroon_knowledge_path_is_rejected(tmp_path: Path):
    tmp_path.joinpath("CODIFICATION.json").write_text("{}", encoding="utf-8")
    with pytest.raises(KnowledgeValidationError, match="contains no crop documents"):
        CameroonKnowledgeProvider(tmp_path)
