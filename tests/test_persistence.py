from __future__ import annotations

from pathlib import Path

from persistence.exporter import KnowledgeDataExchange
from persistence.models import Base, CropEntity, RegionEntity, RuleEntity, SoilEntity


def test_knowledge_data_exchange_exports_all() -> None:
    exchange = KnowledgeDataExchange()
    payload = exchange.export_all_to_relational_payload()

    assert "crops" in payload
    assert "regions" in payload
    assert "soils" in payload
    assert "rules" in payload

    assert len(payload["crops"]) >= 6
    assert len(payload["regions"]) == 10
    assert len(payload["soils"]) >= 6
    assert len(payload["rules"]) >= 35


def test_dump_snapshot_to_json(tmp_path: Path) -> None:
    exchange = KnowledgeDataExchange()
    out_file = tmp_path / "snapshot.json"
    result = exchange.dump_snapshot_to_json(out_file)

    assert result.exists()
    content = result.read_text(encoding="utf-8")
    assert "CULT_TOMATE" in content
    assert "REG_OU" in content
    assert "RULE_CULT_TOMATE" in content
