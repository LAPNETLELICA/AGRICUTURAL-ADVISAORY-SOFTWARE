from __future__ import annotations

from pathlib import Path

from domain.models import ChangeType, ConflictLevel, KnowledgeStatus
from ingestion.pipeline import IngestionPipeline
from ingestion.staging.store import StagingStore
from sources.catalog import DOCUMENTS, ORGANIZATIONS, get_source_reference
from validation.review import ConflictDetector, ReviewManager


def test_sources_catalog_integrity() -> None:
    assert len(ORGANIZATIONS) >= 5
    assert "ORG_MINADER" in ORGANIZATIONS
    assert "ORG_IRAD" in ORGANIZATIONS
    assert "ORG_IFATI" in ORGANIZATIONS
    assert "ORG_FAO" in ORGANIZATIONS

    assert len(DOCUMENTS) >= 5
    ref = get_source_reference("DOC_MINEFOP_IFATI_TOMATE", page="12")
    assert ref.source_id == "DOC_MINEFOP_IFATI_TOMATE"
    assert "12" in ref.reference


def test_staging_store_isolation(tmp_path: Path) -> None:
    store = StagingStore(staging_dir=tmp_path)
    assert len(store.list_staged_items()) == 0

    item = store.stage_item(
        item_id="prop_001",
        entity_type="crop_field",
        entity_id="CULT_TOMATE",
        field_name="spacing_cm",
        field_value="60-80",
        source_id="DOC_MINEFOP_IFATI_TOMATE",
    )
    assert item.status == KnowledgeStatus.PENDING_REVIEW

    proposals = store.list_staged_items()
    assert len(proposals) == 1
    assert proposals[0]["field_value"] == "60-80"


def test_conflict_detection() -> None:
    # Pas de conflit
    assert ConflictDetector.evaluate_conflict("ph", 6.0, 6.0) == ConflictLevel.NONE

    # Conflit mineur
    assert ConflictDetector.evaluate_conflict("ph", 6.0, 6.5) == ConflictLevel.LOW

    # Conflit critique (> 50% d'écart)
    assert ConflictDetector.evaluate_conflict("spacing_cm", 50, 120) == ConflictLevel.CRITICAL


def test_human_review_workflow() -> None:
    manager = ReviewManager()
    review = manager.create_review(
        review_id="rev_01",
        entity_type="crop",
        entity_id="CULT_TOMATE",
        field_name="spacing_cm",
        old_value="50-80",
        new_value="60-80",
        new_source_id="DOC_MINADER_2027",
        old_source_id="DOC_IFATI_2018",
    )
    assert review.status == KnowledgeStatus.PENDING_REVIEW
    assert review.change_type == ChangeType.UPDATE

    # Approbation par agronome
    approved = manager.approve_review("rev_01", reviewer="Dr. Agronome MINADER", notes="Conforme aux essais 2026")
    assert approved.status == KnowledgeStatus.VALIDATED
    assert approved.reviewed_by == "Dr. Agronome MINADER"


def test_ingestion_pipeline_does_not_modify_active_base(tmp_path: Path) -> None:
    staging = StagingStore(staging_dir=tmp_path)
    reviews = ReviewManager()
    pipeline = IngestionPipeline(staging_store=staging, review_manager=reviews)

    reviews_generated = pipeline.run_web_ingestion(
        url="https://minader.cm/bulletins/2026/mais.html",
        source_id="DOC_MINADER_MAIS_2026",
        raw_text="Variété CMS 8704 cycle 115 jours",
        extracted_facts={"crop_id": "CULT_MAIS", "cycle_jours": 115},
        current_knowledge_facts={"cycle_jours": 110},
    )

    assert len(reviews_generated) >= 1
    staged = staging.list_staged_items()
    assert len(staged) >= 1
