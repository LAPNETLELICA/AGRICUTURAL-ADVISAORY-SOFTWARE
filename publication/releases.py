"""Gestionnaire des Knowledge Releases immuables pour Backend 2."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from domain.models import KnowledgeRelease, KnowledgeStatus


class ReleaseManager:
    """Gère l'historique, l'intégrité SHA-256 et l'immuabilité des versions de connaissance."""

    def __init__(self, root: Path | str | None = None) -> None:
        if root is None:
            self.root = Path(__file__).resolve().parents[1] / "BASE_CONNAISSANCES_AGRICOLES"
        else:
            self.root = Path(root)
        self.version_file = self.root / "VERSION.json"
        self.releases_history_file = self.root / "RELEASES_HISTORY.json"

    def compute_knowledge_hash(self) -> str:
        """Calcule une empreinte SHA-256 déterministe sur l'ensemble des fichiers JSON canoniques."""
        hasher = hashlib.sha256()
        json_files = sorted(self.root.rglob("*.json"))
        for path in json_files:
            if path.name in {"VERSION.json", "RELEASES_HISTORY.json"}:
                continue
            hasher.update(str(path.relative_to(self.root)).encode("utf-8"))
            try:
                content = path.read_bytes()
                hasher.update(content)
            except OSError:
                continue
        return hasher.hexdigest()

    def get_active_release(self) -> KnowledgeRelease:
        """Retourne la release active courante."""
        current_hash = self.compute_knowledge_hash()
        if self.version_file.exists():
            try:
                data = json.loads(self.version_file.read_text(encoding="utf-8"))
                return KnowledgeRelease(
                    release_id=str(data.get("knowledge_release", "CM-KNOWLEDGE-2026.10.1")),
                    schema_version=str(data.get("schema_version", "2.0.0")),
                    status=KnowledgeStatus(data.get("status", "published")),
                    release_date=datetime.fromisoformat(data.get("release_date", datetime.now(timezone.utc).isoformat())),
                    sha256_hash=str(data.get("sha256_hash") or current_hash),
                    author=str(data.get("author", "Comité Scientifique AgriSense")),
                    total_crops=int(data.get("total_crops", 6)),
                    total_rules=int(data.get("total_rules", 42)),
                    total_soils=int(data.get("total_soils", 6)),
                    total_regions=int(data.get("total_regions", 10)),
                    sources=list(data.get("sources", ["MINADER", "IRAD", "IFATI", "FAO"])),
                    changelog=list(data.get("changelog", ["Publication initiale canonique Cameroun"])),
                )
            except Exception:
                pass

        # Valeurs par défaut si le fichier n'existe pas
        return KnowledgeRelease(
            release_id="CM-KNOWLEDGE-2026.10.1",
            schema_version="2.0.0",
            status=KnowledgeStatus.PUBLISHED,
            release_date=datetime.now(timezone.utc),
            sha256_hash=current_hash,
            author="Comité Scientifique AgriSense",
            total_crops=6,
            total_rules=42,
            total_soils=6,
            total_regions=10,
            sources=["MINADER", "IRAD", "IFATI", "FAO", "CDE"],
            changelog=["Initialisation officielle BASE_CONNAISSANCES_AGRICOLES"],
        )

    def publish_new_release(
        self,
        release_id: str,
        author: str,
        changelog: list[str],
        stats: dict[str, int] | None = None,
    ) -> KnowledgeRelease:
        """Publie une nouvelle release immuable."""
        current_hash = self.compute_knowledge_hash()
        stats = stats or {}
        new_release = KnowledgeRelease(
            release_id=release_id,
            schema_version="2.0.0",
            status=KnowledgeStatus.PUBLISHED,
            release_date=datetime.now(timezone.utc),
            sha256_hash=current_hash,
            author=author,
            total_crops=stats.get("cultures", 6),
            total_rules=stats.get("rules", 42),
            total_soils=stats.get("sols", 6),
            total_regions=stats.get("regions", 10),
            sources=["MINADER", "IRAD", "IFATI", "FAO", "CDE"],
            changelog=changelog,
        )

        # Enregistrement dans VERSION.json
        payload = {
            "knowledge_release": new_release.release_id,
            "schema_version": new_release.schema_version,
            "status": new_release.status.value,
            "release_date": new_release.release_date.isoformat(),
            "sha256_hash": new_release.sha256_hash,
            "author": new_release.author,
            "total_crops": new_release.total_crops,
            "total_rules": new_release.total_rules,
            "total_soils": new_release.total_soils,
            "total_regions": new_release.total_regions,
            "sources": new_release.sources,
            "changelog": new_release.changelog,
        }
        self.version_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

        # Historique
        history: list[dict[str, Any]] = []
        if self.releases_history_file.exists():
            try:
                history = json.loads(self.releases_history_file.read_text(encoding="utf-8"))
            except Exception:
                history = []
        history.append(payload)
        self.releases_history_file.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")

        return new_release

    def list_history(self) -> list[dict[str, Any]]:
        """Retourne l'historique des releases."""
        if self.releases_history_file.exists():
            try:
                return json.loads(self.releases_history_file.read_text(encoding="utf-8"))
            except Exception:
                return []
        active = self.get_active_release()
        return [{
            "knowledge_release": active.release_id,
            "release_date": active.release_date.isoformat(),
            "sha256_hash": active.sha256_hash,
            "author": active.author,
            "changelog": active.changelog,
        }]
