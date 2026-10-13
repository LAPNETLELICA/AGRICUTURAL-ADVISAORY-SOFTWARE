"""Zone de staging isolée pour les propositions de nouvelles connaissances."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from domain.models import KnowledgeItem, KnowledgeStatus


class StagingStore:
    """Conserve les données extraites d'Internet de manière totalement isolée de la base active."""

    def __init__(self, staging_dir: Path | str | None = None) -> None:
        if staging_dir is None:
            self.staging_dir = Path(__file__).resolve().parent / "data"
        else:
            self.staging_dir = Path(staging_dir)
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        self.proposals_file = self.staging_dir / "proposals.json"

    def stage_item(
        self,
        item_id: str,
        entity_type: str,
        entity_id: str,
        field_name: str,
        field_value: Any,
        source_id: str,
    ) -> KnowledgeItem:
        item = KnowledgeItem(
            item_id=item_id,
            entity_type=entity_type,
            entity_id=entity_id,
            field_name=field_name,
            field_value=field_value,
            source_id=source_id,
            status=KnowledgeStatus.PENDING_REVIEW,
            version="staging-candidate",
            created_at=datetime.now(timezone.utc),
        )
        proposals = self.list_staged_items()
        proposals.append(item.model_dump(mode="json"))
        self.proposals_file.write_text(json.dumps(proposals, indent=2, ensure_ascii=False), encoding="utf-8")
        return item

    def list_staged_items(self) -> list[dict[str, Any]]:
        if self.proposals_file.exists():
            try:
                return json.loads(self.proposals_file.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def clear(self) -> None:
        if self.proposals_file.exists():
            self.proposals_file.unlink()
