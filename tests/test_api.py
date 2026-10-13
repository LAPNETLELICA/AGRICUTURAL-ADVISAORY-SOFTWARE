from __future__ import annotations

from fastapi.testclient import TestClient

from api.app import create_app

client = TestClient(create_app())


def test_health() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "backend2-knowledge"


def test_version() -> None:
    response = client.get("/api/v1/knowledge/version")
    assert response.status_code == 200
    data = response.json()
    assert "knowledge_release" in data
    assert "CM-KNOWLEDGE-" in data["knowledge_release"]
    assert "sha256_hash" in data
    assert len(data["sha256_hash"]) == 64
    assert data["statistics"]["total_rules"] >= 30


def test_list_and_get_crops() -> None:
    response = client.get("/api/v1/crops")
    assert response.status_code == 200
    crops = response.json()
    assert len(crops) >= 6
    codes = {c["code"] for c in crops}
    assert "CULT_TOMATE" in codes
    assert "CULT_POMME_DE_TERRE" in codes
    assert "CULT_MAIS" in codes

    # Get single crop by code
    resp_tom = client.get("/api/v1/crops/CULT_TOMATE")
    assert resp_tom.status_code == 200
    assert resp_tom.json()["nom_courant"] == "Tomate"

    # Get single crop by alias
    resp_alias = client.get("/api/v1/crops/tomato")
    assert resp_alias.status_code == 200
    assert resp_alias.json()["code"] == "CULT_TOMATE"


def test_list_and_get_regions() -> None:
    response = client.get("/api/v1/regions")
    assert response.status_code == 200
    regions = response.json()
    assert len(regions) == 10

    resp_west = client.get("/api/v1/regions/REG_OU")
    assert resp_west.status_code == 200
    assert resp_west.json()["nom"] == "Ouest"


def test_list_and_get_soils() -> None:
    response = client.get("/api/v1/soils")
    assert response.status_code == 200
    assert len(response.json()) >= 6

    resp_volc = client.get("/api/v1/soils/SOL_VOLCANIQUE")
    assert resp_volc.status_code == 200
    assert "Andosols" in resp_volc.json()["nom"]


def test_list_and_get_rules() -> None:
    response = client.get("/api/v1/rules")
    assert response.status_code == 200
    rules = response.json()
    assert len(rules) >= 30

    rule_id = rules[0]["rule_id"]
    single_resp = client.get(f"/api/v1/rules/{rule_id}")
    assert single_resp.status_code == 200
    assert single_resp.json()["rule_id"] == rule_id


def test_list_and_get_sources() -> None:
    response = client.get("/api/v1/sources")
    assert response.status_code == 200
    sources = response.json()
    assert len(sources) >= 5

    doc_id = sources[0]["source_id"]
    single_resp = client.get(f"/api/v1/sources/{doc_id}")
    assert single_resp.status_code == 200
    assert single_resp.json()["source_id"] == doc_id


def test_query_knowledge_returns_rules_and_sources() -> None:
    payload = {
        "crop_id": "CULT_TOMATE",
        "trees": ["T1", "T2", "T4", "T5", "T7"],
        "region_id": "REG_OU",
        "soil_id": "SOL_VOLCANIQUE",
    }
    response = client.post("/api/v1/knowledge/query", json=payload)
    assert response.status_code == 200
    body = response.json()

    assert body["crop_id"] == "CULT_TOMATE"
    assert set(body["requested_trees"]) == {"T1", "T2", "T4", "T5", "T7"}
    assert len(body["rules"]) >= 4
    assert len(body["sources"]) >= 1

    # Verify rule structure contains conditions and candidate
    r0 = body["rules"][0]
    assert "conditions" in r0
    assert "candidate" in r0
    assert "actions" in r0["candidate"]
    assert len(r0["candidate"]["actions"]) > 0


def test_query_with_crop_alias() -> None:
    payload = {
        "crop_id": "potato",
        "trees": ["T2", "T6"],
    }
    response = client.post("/api/v1/knowledge/query", json=payload)
    assert response.status_code == 200
    assert response.json()["crop_id"] == "CULT_POMME_DE_TERRE"


def test_unknown_crop_returns_404() -> None:
    response = client.get("/api/v1/crops/CULT_INCONNUE_XYZ")
    assert response.status_code == 404
