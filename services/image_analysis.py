"""Conservative visual-evidence boundary for the advisory engine.

The default implementation does not claim a diagnosis from pixels.  It indexes
existing knowledge images and emits bounded evidence only when a photo is a
valid agricultural media item; a model-backed analyzer can be substituted later.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from uuid import uuid4

from services.media import MediaService

_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


@dataclass(frozen=True, slots=True)
class VisualAnalysis:
    analysis_id: str
    image_id: str
    analysis_type: str
    relevant: bool
    summary: str
    visual_evidence: dict[str, object]
    matches: list[dict[str, object]]


class ImageAnalysisService:
    def __init__(self, media: MediaService, knowledge_path: Path) -> None:
        self._media = media
        self._knowledge_path = knowledge_path

    def reference_index(self) -> list[dict[str, str]]:
        if not self._knowledge_path.exists():
            return []
        files = [
            {
                "knowledge_path": str(path.relative_to(self._knowledge_path)),
                "subject": path.parent.name,
            }
            for path in self._knowledge_path.rglob("*")
            if path.is_file() and path.suffix.lower() in _IMAGE_SUFFIXES
        ]
        catalogue = self._knowledge_path / "PHOTOS" / "metadata_catalogue.json"
        if not catalogue.is_file():
            return files
        try:
            entries = json.loads(catalogue.read_text(encoding="utf-8")).get("catalogue", [])
        except (OSError, json.JSONDecodeError):
            return files
        metadata = [
            {
                "knowledge_path": f"PHOTOS/{entry['fichier']}",
                "subject": str(entry.get("categorie", "agricultural")),
            }
            for entry in entries
            if isinstance(entry, dict) and isinstance(entry.get("fichier"), str)
        ]
        return files + [entry for entry in metadata if entry not in files]

    def analyze(
        self, *, farmer_id: str, image_id: str, analysis_type: str, crop_id: str | None = None
    ) -> VisualAnalysis:
        item, content = self._media.get(image_id)
        if item.farmer_id != farmer_id:
            raise PermissionError("image evidence is not owned by this user")
        expected = analysis_type.strip().lower()
        if expected not in {"soil", "plant", "crop", "general"}:
            raise ValueError("analysis_type must be soil, plant, crop, or general")
        # MIME/signature validation happened at upload.  Without a configured,
        # governed CV provider we do not infer disease or soil composition.
        relevant = len(content) >= 1024
        if not relevant:
            summary = (
                f"This image does not contain enough clear {expected} information. "
                "Please provide a clearer photo."
            )
            evidence: dict[str, object] = {"usable": False, "reason": "image_too_small"}
        else:
            summary = (
                "Image accepted as supplementary visual evidence; confirm it with "
                "field observations and rules."
            )
            evidence = {
                "usable": True,
                "analysis_type": expected,
                "crop_id": crop_id,
                "confidence": "unverified",
            }
        return VisualAnalysis(str(uuid4()), image_id, expected, relevant, summary, evidence, [])

    @staticmethod
    def public(result: VisualAnalysis) -> dict[str, object]:
        return asdict(result)
