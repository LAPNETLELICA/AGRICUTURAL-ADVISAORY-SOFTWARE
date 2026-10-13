"""Lecteur et navigateur universel pour BASE_CONNAISSANCES_AGRICOLES (Cameroun).

Conforme à la spécification Structure_des_connaissances_agricoles_Cameroun.pdf.
Permet d'interroger la base documentaire par culture, famille, variété, sol, région,
localité, climat, calendrier cultural, risques ou pratiques, et de résoudre
les liens inter-dossiers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class CameroonKnowledgeBase:
    """Accesseur et explorateur de la base de connaissances agricoles du Cameroun."""

    def __init__(self, root: Path | str | None = None) -> None:
        if root is None:
            self.root = Path(__file__).resolve().parent
        else:
            self.root = Path(root)

        self.codification_file = self.root / "CODIFICATION.json"
        self._codification: dict[str, Any] = self._read_json(self.codification_file) or {}

    def _read_json(self, path: Path) -> Any:
        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return None

    # --- CULTURES ET FAMILLES ---

    def list_familles(self) -> list[dict[str, Any]]:
        results = []
        fam_dir = self.root / "CULTURE" / "FAMILLES"
        for p in sorted(fam_dir.glob("*.json")):
            data = self._read_json(p)
            if data:
                results.append(data)
        return results

    def get_famille(self, code: str) -> dict[str, Any] | None:
        target_code = code.upper()
        for fam in self.list_familles():
            if fam.get("code") == target_code:
                return fam
        return None

    def list_cultures(self) -> list[dict[str, Any]]:
        results = []
        cult_dir = self.root / "CULTURE" / "CULTURES"
        for p in sorted(cult_dir.glob("*.json")):
            data = self._read_json(p)
            if data:
                results.append(data)
        return results

    def get_culture(self, code: str) -> dict[str, Any] | None:
        target_code = code.upper()
        if not target_code.startswith("CULT_"):
            target_code = f"CULT_{target_code}"
        for c in self.list_cultures():
            if c.get("code") == target_code:
                return c
        return None

    def get_varietes_culture(self, culture_code: str) -> list[dict[str, Any]]:
        target_code = culture_code.upper()
        if not target_code.startswith("CULT_"):
            target_code = f"CULT_{target_code}"
        var_dir = self.root / "CULTURE" / "VARIETES"
        for p in sorted(var_dir.glob("*.json")):
            data = self._read_json(p)
            if data and data.get("culture_code") == target_code:
                return data.get("varietes", [])
        return []

    # --- SOLS ---

    def list_sols(self) -> list[dict[str, Any]]:
        results = []
        soil_dir = self.root / "SOL" / "TYPES_SOL"
        for p in sorted(soil_dir.glob("*.json")):
            data = self._read_json(p)
            if data:
                results.append(data)
        return results

    def get_sol(self, code: str) -> dict[str, Any] | None:
        target_code = code.upper()
        if not target_code.startswith("SOL_"):
            target_code = f"SOL_{target_code}"
        for s in self.list_sols():
            if s.get("code") == target_code:
                return s
        return None

    def get_sols_favorables(self, culture_code: str) -> list[dict[str, Any]]:
        cult = self.get_culture(culture_code)
        if not cult:
            return []
        favorable_codes = cult.get("liens_dossiers", {}).get("sols_favorables", [])
        return [s for s in self.list_sols() if s.get("code") in favorable_codes]

    def get_caracteristiques_sol(self) -> dict[str, Any]:
        phys = self._read_json(self.root / "SOL" / "CARACTERISTIQUES" / "physiques_et_observation.json") or {}
        chim = self._read_json(self.root / "SOL" / "CARACTERISTIQUES" / "chimiques_et_fertilite.json") or {}
        return {"physiques": phys, "chimiques": chim}

    # --- REGIONS ET LOCALITES ---

    def list_regions(self) -> list[dict[str, Any]]:
        results = []
        reg_dir = self.root / "REGION" / "10_REGIONS"
        for p in sorted(reg_dir.glob("*.json")):
            data = self._read_json(p)
            if data:
                results.append(data)
        return results

    def get_region(self, code: str) -> dict[str, Any] | None:
        target_code = code.upper()
        if not target_code.startswith("REG_"):
            target_code = f"REG_{target_code}"
        for r in self.list_regions():
            if r.get("code") == target_code:
                return r
        return None

    def list_localites(self, region_code: str | None = None) -> list[dict[str, Any]]:
        results = []
        loc_dir = self.root / "REGION" / "LOCALITES"
        target_reg = region_code.upper() if region_code else None
        if target_reg and not target_reg.startswith("REG_"):
            target_reg = f"REG_{target_reg}"
        for p in sorted(loc_dir.glob("*.json")):
            data = self._read_json(p)
            if data:
                if target_reg is None or data.get("region_code") == target_reg:
                    results.extend(data.get("localites", []))
        return results

    # --- CLIMAT ET CALENDRIER ---

    def list_zones_climatiques(self) -> list[dict[str, Any]]:
        clim_file = self.root / "CLIMAT" / "zones_agroecologiques.json"
        data = self._read_json(clim_file) or {}
        return data.get("zones", [])

    def get_calendrier_region(self, region_code: str) -> dict[str, Any] | None:
        reg_code = region_code.upper()
        if reg_code in {"REG_OU", "REG_NW"}:
            return self._read_json(self.root / "CALENDRIER_CULTURAL" / "calendrier_ouest_nord_ouest.json")
        if reg_code in {"REG_CE", "REG_SU", "REG_ES"}:
            return self._read_json(self.root / "CALENDRIER_CULTURAL" / "calendrier_centre_sud.json")
        if reg_code in {"REG_NO", "REG_EN"}:
            return self._read_json(self.root / "CALENDRIER_CULTURAL" / "calendrier_grand_nord.json")
        return None

    # --- RISQUES ET PRATIQUES ---

    def list_engrais(self) -> list[dict[str, Any]]:
        min_file = self.root / "RISQUES_ET_PRATIQUES" / "ENGRAIS_ET_FERTILISATION" / "engrais_mineraux.json"
        org_file = self.root / "RISQUES_ET_PRATIQUES" / "ENGRAIS_ET_FERTILISATION" / "fertilisation_locale_organique.json"
        min_data = (self._read_json(min_file) or {}).get("engrais", [])
        org_data = (self._read_json(org_file) or {}).get("fertilisants", [])
        return min_data + org_data

    def get_engrais(self, code: str) -> dict[str, Any] | None:
        target_code = code.upper()
        for e in self.list_engrais():
            if e.get("code") == target_code:
                return e
        return None

    def list_ravageurs(self, culture_code: str | None = None) -> list[dict[str, Any]]:
        results = []
        rav_dir = self.root / "RISQUES_ET_PRATIQUES" / "RAVAGEURS_ET_PESTES"
        target_code = culture_code.upper() if culture_code else None
        if target_code and not target_code.startswith("CULT_"):
            target_code = f"CULT_{target_code}"

        for p in sorted(rav_dir.glob("*.json")):
            data = self._read_json(p)
            if not data:
                continue
            if target_code is None or data.get("culture_code") == target_code:
                items = data.get("ravageurs_principaux") or data.get("ravageurs") or []
                results.extend(items)
        return results

    # --- TOPOGRAPHIE ET PHOTOS ---

    def get_topographie(self) -> dict[str, Any]:
        relief = self._read_json(self.root / "TOPOGRAPHIE" / "reliefs_et_altitudes.json") or {}
        amenagements = self._read_json(self.root / "TOPOGRAPHIE" / "amenagements_anti_erosifs.json") or {}
        return {"reliefs": relief, "amenagements": amenagements}

    def list_photos(self, culture_code: str | None = None) -> list[dict[str, Any]]:
        photo_file = self.root / "PHOTOS" / "metadata_catalogue.json"
        data = self._read_json(photo_file) or {}
        items = data.get("catalogue", [])
        if culture_code:
            target = culture_code.upper()
            if not target.startswith("CULT_"):
                target = f"CULT_{target}"
            return [it for it in items if it.get("culture_concernee") == target]
        return items

    # --- RESOLUTION CROISEE (LIENS ENTRE DOSSIERS) ---

    def resolve_culture_links(self, culture_code: str) -> dict[str, Any]:
        """Résout tous les liens d'une culture vers les autres dossiers."""
        cult = self.get_culture(culture_code)
        if not cult:
            return {"error": f"Culture '{culture_code}' introuvable."}

        liens = cult.get("liens_dossiers", {})
        sols = [self.get_sol(c) for c in liens.get("sols_favorables", [])]
        regions = [self.get_region(c) for c in liens.get("regions_principales", [])]
        engrais = [self.get_engrais(c) for c in liens.get("engrais_recommandes", [])]
        ravageurs = self.list_ravageurs(cult["code"])
        varietes = self.get_varietes_culture(cult["code"])
        photos = self.list_photos(cult["code"])

        return {
            "culture": cult,
            "varietes": varietes,
            "sols_favorables": [s for s in sols if s],
            "regions_principales": [r for r in regions if r],
            "engrais_recommandes": [e for e in engrais if e],
            "ravageurs": ravageurs,
            "photos": photos,
        }

    def summary(self) -> dict[str, Any]:
        return {
            "familles_count": len(self.list_familles()),
            "cultures_count": len(self.list_cultures()),
            "sols_count": len(self.list_sols()),
            "regions_count": len(self.list_regions()),
            "localites_count": len(self.list_localites()),
            "zones_climatiques_count": len(self.list_zones_climatiques()),
            "engrais_count": len(self.list_engrais()),
            "photos_indexees": len(self.list_photos()),
        }
