import json
from pathlib import Path

import pytest

from validation import KnowledgeValidationError, validate_knowledge_tree


def test_validation_accepts_canonical_base() -> None:
    root = Path(__file__).resolve().parents[1] / "BASE_CONNAISSANCES_AGRICOLES"
    report = validate_knowledge_tree(root)
    assert report["json_files"] > 0
    assert report["duplicate_top_level_codes"] == 0


def test_validation_rejects_invalid_json(tmp_path: Path) -> None:
    (tmp_path / "bad.json").write_text("{", encoding="utf-8")
    with pytest.raises(KnowledgeValidationError):
        validate_knowledge_tree(tmp_path)


def test_validation_rejects_duplicate_top_level_codes(tmp_path: Path) -> None:
    (tmp_path / "a.json").write_text(json.dumps({"code": "CULT_X"}), encoding="utf-8")
    (tmp_path / "b.json").write_text(json.dumps({"code": "CULT_X"}), encoding="utf-8")
    with pytest.raises(KnowledgeValidationError):
        validate_knowledge_tree(tmp_path)
