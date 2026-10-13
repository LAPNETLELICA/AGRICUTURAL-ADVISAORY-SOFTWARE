#!/usr/bin/env python3
"""Script officiel de validation stricte de BASE_CONNAISSANCES_AGRICOLES."""

from __future__ import annotations

import sys
from pathlib import Path

# Assurer l'accès aux packages de backend2
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from validation.validator import KnowledgeValidationError, validate_knowledge_tree


def main() -> int:
    root = Path(__file__).resolve().parents[1] / "BASE_CONNAISSANCES_AGRICOLES"
    print(f"Lancement de la validation stricte sur : {root}")
    try:
        report = validate_knowledge_tree(root)
    except KnowledgeValidationError as exc:
        print(f"\n❌ {exc}", file=sys.stderr)
        return 1

    print("\n✅ VALIDATION STRICTE RÉUSSIE : BASE DE CONNAISSANCES 100% VALIDE ET COHÉRENTE")
    for key, value in report.items():
        print(f"  • {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
