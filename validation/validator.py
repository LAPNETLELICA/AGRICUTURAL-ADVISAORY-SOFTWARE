"""Validation stricte et exhaustive de BASE_CONNAISSANCES_AGRICOLES."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


class KnowledgeValidationError(RuntimeError):
    def __init__(self, message: str, details: list[dict[str, Any]] | None = None) -> None:
        super().__init__(message)
        self.details = details or []


def validate_knowledge_tree(root: Path) -> dict[str, Any]:
    """Exécute une vérification stricte : syntaxe JSON, unicité des codes, et cohérence référentielle."""
    if not root.exists() or not root.is_dir():
        raise KnowledgeValidationError(f"Base de connaissances introuvable : {root}")

    errors: list[dict[str, Any]] = []
    json_files = sorted(root.rglob("*.json"))
    if not json_files:
        raise KnowledgeValidationError(f"Aucun fichier JSON dans {root}")

    # 1. Vérification de la syntaxe JSON et extraction des identifiants
    loaded_docs: dict[Path, dict[str, Any]] = {}
    top_level_codes: dict[str, Path] = {}
    duplicate_codes: list[tuple[str, Path, Path]] = []

    for path in json_files:
        rel_path = path.relative_to(root)
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeError as exc:
            errors.append({
                "fichier": str(rel_path),
                "champ": "encodage",
                "type_erreur": "UnicodeDecodeError",
                "message": f"Fichier non encodé en UTF-8 : {exc}",
            })
            continue

        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            errors.append({
                "fichier": str(rel_path),
                "ligne": exc.lineno,
                "colonne": exc.colno,
                "type_erreur": "JSONSyntaxError",
                "message": f"Syntaxe JSON corrompue : {exc.msg}",
            })
            continue

        if not isinstance(data, (dict, list)):
            errors.append({
                "fichier": str(rel_path),
                "type_erreur": "InvalidStructure",
                "message": "Le contenu racine doit être un objet JSON ou une liste",
            })
            continue

        if isinstance(data, dict):
            loaded_docs[path] = data
            code = data.get("code")
            if isinstance(code, str) and code:
                if code in top_level_codes:
                    duplicate_codes.append((code, top_level_codes[code], rel_path))
                else:
                    top_level_codes[code] = rel_path

    # Codes dupliqués
    if duplicate_codes:
        for code, first_p, second_p in duplicate_codes:
            errors.append({
                "fichier": str(second_p),
                "champ": "code",
                "type_erreur": "DuplicateCodeError",
                "message": f"Identifiant dupliqué '{code}', déjà défini dans {first_p}",
            })

    # 2. Vérification des collections obligatoires
    defined_crops = set()
    defined_regions = set()
    defined_soils = set()
    defined_families = set()

    for path, data in loaded_docs.items():
        code = str(data.get("code", ""))
        if code.startswith("CULT_"):
            defined_crops.add(code)
        elif code.startswith("REG_"):
            defined_regions.add(code)
        elif code.startswith("SOL_"):
            defined_soils.add(code)
        elif code.startswith("FAM_"):
            defined_families.add(code)

    # 3. Vérification de l'intégrité référentielle
    for path, data in loaded_docs.items():
        rel_path = path.relative_to(root)

        # Vérification des cultures : famille_code et liens_dossiers
        if str(data.get("code", "")).startswith("CULT_"):
            fam_code = data.get("famille_code")
            if fam_code and fam_code not in defined_families:
                errors.append({
                    "fichier": str(rel_path),
                    "champ": "famille_code",
                    "type_erreur": "OrphanReferenceError",
                    "message": f"Référence vers une famille inexistante '{fam_code}'",
                })

            links = data.get("liens_dossiers", {})
            for reg in links.get("regions_principales", []):
                if reg not in defined_regions:
                    errors.append({
                        "fichier": str(rel_path),
                        "champ": "liens_dossiers.regions_principales",
                        "type_erreur": "OrphanReferenceError",
                        "message": f"Référence vers une région inexistante '{reg}'",
                    })

        # Vérification des variétés
        if "varietes" in data and isinstance(data["varietes"], list):
            cult_code = data.get("culture_code")
            if cult_code and cult_code not in defined_crops:
                errors.append({
                    "fichier": str(rel_path),
                    "champ": "culture_code",
                    "type_erreur": "OrphanReferenceError",
                    "message": f"Variétés associées à une culture inexistante '{cult_code}'",
                })

    if errors:
        error_lines = [
            f"[{e['type_erreur']}] {e['fichier']}" + (f":{e.get('champ')}" if 'champ' in e else "") + f" - {e['message']}"
            for e in errors
        ]
        raise KnowledgeValidationError(
            f"ÉCHEC DE VALIDATION STRICTE ({len(errors)} erreurs trouvées) :\n" + "\n".join(error_lines),
            details=errors,
        )

    return {
        "json_files": len(json_files),
        "total_documents": len(loaded_docs),
        "cultures": len(defined_crops),
        "regions": len(defined_regions),
        "sols": len(defined_soils),
        "familles": len(defined_families),
        "duplicate_top_level_codes": 0,
        "orphan_references": 0,
        "valid": True,
    }
