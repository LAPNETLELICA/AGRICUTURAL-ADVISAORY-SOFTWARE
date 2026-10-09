#!/usr/bin/env python3
"""Script de validation d'intégrité de la base BASE_CONNAISSANCES_AGRICOLES."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add backend2 root to sys.path
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from BASE_CONNAISSANCES_AGRICOLES.reader import CameroonKnowledgeBase

REQUIRED_DIRS = (
    "CULTURE/FAMILLES",
    "CULTURE/CULTURES",
    "CULTURE/VARIETES",
    "SOL/TYPES_SOL",
    "SOL/CARACTERISTIQUES",
    "SOL/SOL_PAR_CULTURE",
    "SOL/SOL_PAR_REGION",
    "SOL/ENTRETIEN_RESTAURATION",
    "REGION/10_REGIONS",
    "REGION/LOCALITES",
    "CLIMAT",
    "CALENDRIER_CULTURAL",
    "RISQUES_ET_PRATIQUES/BONNES_PRATIQUES",
    "RISQUES_ET_PRATIQUES/ENGRAIS_ET_FERTILISATION",
    "RISQUES_ET_PRATIQUES/RAVAGEURS_ET_PESTES",
    "RISQUES_ET_PRATIQUES/RISQUES_AGRICOLES",
    "RISQUES_ET_PRATIQUES/RESTAURATION_REPOS_ROTATION",
    "TOPOGRAPHIE",
    "PHOTOS",
    "MALADIES_DES_PLANTES",
)

REQUIRED_10_REGIONS = {
    "REG_AD", "REG_CE", "REG_ES", "REG_EN", "REG_LT",
    "REG_NO", "REG_NW", "REG_OU", "REG_SU", "REG_SW"
}


def validate_base() -> int:
    base_dir = BACKEND_ROOT / "BASE_CONNAISSANCES_AGRICOLES"
    print(f"Validation de BASE_CONNAISSANCES_AGRICOLES dans : {base_dir}")

    errors: list[str] = []

    # 1. Vérification des répertoires requis
    for d in REQUIRED_DIRS:
        target = base_dir / d
        if not target.is_dir():
            errors.append(f"Répertoire manquant : {d}")

    # 2. Vérification syntaxique de tous les JSON
    json_count = 0
    for p in base_dir.rglob("*.json"):
        json_count += 1
        try:
            with p.open("r", encoding="utf-8") as f:
                json.load(f)
        except Exception as e:
            errors.append(f"Erreur JSON dans {p.relative_to(base_dir)} : {e}")

    # 3. Test du lecteur et des 10 régions
    kb = CameroonKnowledgeBase(base_dir)
    regions = kb.list_regions()
    region_codes = {r.get("code") for r in regions}
    missing_regions = REQUIRED_10_REGIONS - region_codes
    if missing_regions:
        errors.append(f"Régions administratives manquantes : {missing_regions}")

    # 4. Vérification des liens croisés pour chaque culture
    cultures = kb.list_cultures()
    if not cultures:
        errors.append("Aucune culture trouvée dans CULTURE/CULTURES.")

    for cult in cultures:
        c_code = cult.get("code")
        resolved = kb.resolve_culture_links(c_code)
        if "error" in resolved:
            errors.append(f"Échec de résolution pour {c_code} : {resolved['error']}")
            continue

        liens = cult.get("liens_dossiers", {})
        # Vérifier sols
        for s_code in liens.get("sols_favorables", []):
            if not kb.get_sol(s_code):
                errors.append(f"{c_code} référence un sol inexistant : {s_code}")
        # Vérifier régions
        for r_code in liens.get("regions_principales", []):
            if not kb.get_region(r_code):
                errors.append(f"{c_code} référence une région inexistante : {r_code}")
        # Vérifier engrais
        for e_code in liens.get("engrais_recommandes", []):
            if not kb.get_engrais(e_code):
                errors.append(f"{c_code} référence un engrais inexistant : {e_code}")

    if errors:
        print("\n❌ ÉCHEC DE VALIDATION DE LA BASE DE CONNAISSANCES CAMEROUN :")
        for err in errors:
            print(f"  - {err}")
        return 1

    summary = kb.summary()
    print("\n✅ VALIDATION RÉUSSIE : BASE DE CONNAISSANCES 100% CONFORME")
    print(f"  - Fichiers JSON vérifiés : {json_count}")
    print(f"  - Familles agricoles : {summary['familles_count']}")
    print(f"  - Cultures documentées : {summary['cultures_count']}")
    print(f"  - Types de sols répertoriés : {summary['sols_count']}")
    print(f"  - Régions administratives : {summary['regions_count']} (couverture 10/10)")
    print(f"  - Localités / Bassins : {summary['localites_count']}")
    print(f"  - Zones climatiques agro-écologiques : {summary['zones_climatiques_count']}")
    print(f"  - Engrais et fertilisants : {summary['engrais_count']}")
    print(f"  - Ressources photographiques indexées : {summary['photos_indexees']}")
    print(f"  - Dossier MALADIES_DES_PLANTES réservé et spécifié pour la phase ultérieure.")
    return 0


if __name__ == "__main__":
    raise SystemExit(validate_base())
