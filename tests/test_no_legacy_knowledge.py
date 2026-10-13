from __future__ import annotations

import re
from pathlib import Path


def test_legacy_knowledge_directory_removed() -> None:
    root = Path(__file__).resolve().parents[1]
    assert not (root / "knowledge").exists()


def test_reasoning_engine_removed_from_backend2() -> None:
    root = Path(__file__).resolve().parents[1]
    assert not (root / "engine").exists()


def test_no_imports_of_backend1_modules() -> None:
    """Vérifie qu'aucun module de backend2 n'importe engine.models ou engine.advisory."""
    root = Path(__file__).resolve().parents[1]
    py_files = list(root.rglob("*.py"))
    assert len(py_files) > 10

    forbidden_patterns = [
        re.compile(r"^\s*from\s+engine(?:\.|\s)", re.MULTILINE),
        re.compile(r"^\s*import\s+engine(?:\.|\s)", re.MULTILINE),
        re.compile(r"\bAdvisoryEngine\b"),
        re.compile(r"\bRuleEvaluator\b"),
        re.compile(r"\bCropTreeSelector\b"),
    ]

    for f in py_files:
        # Ignore les fichiers de test eux-mêmes
        if "test_no_legacy_knowledge.py" in str(f):
            continue
        content = f.read_text(encoding="utf-8")
        for pattern in forbidden_patterns:
            assert not pattern.search(content), f"Import ou référence interdite vers Backend1 '{pattern.pattern}' dans {f}"
