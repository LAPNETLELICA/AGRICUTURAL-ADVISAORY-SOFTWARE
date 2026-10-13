"""Pipeline d'ingestion complet et sécurisé pour sources web (MINADER, IRAD, FAO)."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from domain.models import ChangeType, ConflictLevel, KnowledgeItem, KnowledgeStatus, ValidationReview
from ingestion.staging.store import StagingStore
from validation.review import ConflictDetector, ReviewManager


class IngestionPipeline:
    """Orchestrateur du flux :
    DISCOVER -> FETCH -> SNAPSHOT -> EXTRACT -> NORMALIZE -> COMPARE -> STAGE -> REVIEW -> VALIDATE -> PUBLISH.
    """

    def __init__(self, staging_store: StagingStore | None = None, review_manager: ReviewManager | None = None) -> None:
        self.staging = staging_store or StagingStore()
        self.reviews = review_manager or ReviewManager()

    def run_web_ingestion(
        self,
        url: str,
        source_id: str,
        raw_text: str,
        extracted_facts: dict[str, Any],
        current_knowledge_facts: dict[str, Any],
    ) -> list[ValidationReview]:
        """Exécute les étapes du pipeline jusqu'à la mise en staging et la création de fiches de revue."""
        # 1. SNAPSHOT (empreinte SHA-256 du contenu brut récupéré)
        content_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()

        generated_reviews: list[ValidationReview] = []

        # 2. EXTRACT, NORMALIZE, COMPARE & STAGE
        for field, new_val in extracted_facts.items():
            old_val = current_knowledge_facts.get(field)
            item_id = f"item_{source_id}_{field}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

            # Sécurité absolue : stocker uniquement en Staging
            self.staging.stage_item(
                item_id=item_id,
                entity_type="agronomic_field",
                entity_id=extracted_facts.get("crop_id", "GLOBAL"),
                field_name=field,
                field_value=new_val,
                source_id=source_id,
            )

            # Création de la fiche de revue humaine
            review = self.reviews.create_review(
                review_id=f"rev_{item_id}",
                entity_type="crop_field",
                entity_id=str(extracted_facts.get("crop_id", "GLOBAL")),
                field_name=field,
                old_value=old_val,
                new_value=new_val,
                new_source_id=source_id,
            )
            generated_reviews.append(review)

        return generated_reviews
