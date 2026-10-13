from __future__ import annotations

from pathlib import Path

from publication.releases import ReleaseManager


def test_active_release_is_computed() -> None:
    mgr = ReleaseManager()
    release = mgr.get_active_release()
    assert release.release_id.startswith("CM-KNOWLEDGE-")
    assert len(release.sha256_hash) == 64
    assert release.total_crops >= 6


def test_sha256_hash_is_deterministic() -> None:
    mgr = ReleaseManager()
    hash1 = mgr.compute_knowledge_hash()
    hash2 = mgr.compute_knowledge_hash()
    assert hash1 == hash2


def test_publish_new_release(tmp_path: Path) -> None:
    # Simuler une base temporaire
    (tmp_path / "test.json").write_text('{"code": "TEST"}', encoding="utf-8")
    mgr = ReleaseManager(root=tmp_path)

    new_rel = mgr.publish_new_release(
        release_id="CM-KNOWLEDGE-2026.11.0",
        author="Comité Scientifique",
        changelog=["Mise à jour des variétés"],
        stats={"cultures": 6, "rules": 42},
    )
    assert new_rel.release_id == "CM-KNOWLEDGE-2026.11.0"
    assert len(new_rel.sha256_hash) == 64

    # Relire la release active
    active = mgr.get_active_release()
    assert active.release_id == "CM-KNOWLEDGE-2026.11.0"

