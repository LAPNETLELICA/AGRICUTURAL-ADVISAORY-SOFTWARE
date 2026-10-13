"""Logique de revue humaine et résolution de conflits de connaissances agricoles."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from domain.models import ChangeType, ConflictLevel, KnowledgeStatus, ValidationReview


class ConflictDetector:
    """Détecte les écarts entre les connaissances canoniques actives et les propositions en staging."""

    @staticmethod
    def evaluate_conflict(field_name: str, current_value: Any, proposed_value: Any) -> ConflictLevel:
        if current_value == proposed_value:
            return ConflictLevel.NONE

        # Si les deux valeurs sont numériques, évaluer le pourcentage d'écart
        if isinstance(current_value, (int, float)) and isinstance(proposed_value, (int, float)):
            diff_ratio = abs(current_value - proposed_value) / max(abs(current_value), 1)
            if diff_ratio > 0.5:
                return ConflictLevel.CRITICAL
            elif diff_ratio > 0.2:
                return ConflictLevel.HIGH
            return ConflictLevel.LOW

        # Si c'est une liste ou un dictionnaire
        if isinstance(current_value, list) and isinstance(proposed_value, list):
            diff = set(str(x) for x in proposed_value) - set(str(x) for x in current_value)
            if len(diff) > 2:
                return ConflictLevel.MEDIUM
            return ConflictLevel.LOW

        return ConflictLevel.MEDIUM


class ReviewManager:
    """Gère le cycle de validation humaine des propositions de connaissances."""

    def __init__(self) -> None:
        self._reviews: dict[str, ValidationReview] = {}

    def create_review(
        self,
        review_id: str,
        entity_type: str,
        entity_id: str,
        field_name: str,
        old_value: Any,
        new_value: Any,
        new_source_id: str,
        old_source_id: str | None = None,
    ) -> ValidationReview:
        conflict_level = ConflictDetector.evaluate_conflict(field_name, old_value, new_value)
        review = ValidationReview(
            review_id=review_id,
            entity_type=entity_type,
            entity_id=entity_id,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            old_source_id=old_source_id,
            new_source_id=new_source_id,
            conflict_level=conflict_level,
            change_type=ChangeType.UPDATE if old_value is not None else ChangeType.ADDITION,
            status=KnowledgeStatus.PENDING_REVIEW,
        )
        self._reviews[review_id] = review
        return review

    def approve_review(self, review_id: str, reviewer: str, notes: str = "") -> ValidationReview:
        if review_id not in self._reviews:
            raise KeyError(f"Revue {review_id} introuvable.")
        review = self._reviews[review_id]
        updated = review.model_copy(
            update={
                "status": KnowledgeStatus.VALIDATED,
                "reviewed_by": reviewer,
                "reviewer_notes": notes,
                "reviewed_at": datetime.now(timezone.utc),
            }
        )
        self._reviews[review_id] = updated
        return updated

    def reject_review(self, review_id: str, reviewer: str, reason: str) -> ValidationReview:
        if review_id not in self._reviews:
            raise KeyError(f"Revue {review_id} introuvable.")
        review = self._reviews[review_id]
        updated = review.model_copy(
            update={
                "status": KnowledgeStatus.REJECTED,
                "reviewed_by": reviewer,
                "reviewer_notes": reason,
                "reviewed_at": datetime.now(timezone.utc),
            }
        )
        self._reviews[review_id] = updated
        return updated

    def list_pending_reviews(self) -> list[ValidationReview]:
        return [r for r in self._reviews.values() if r.status == KnowledgeStatus.PENDING_REVIEW]

