#!/usr/bin/env python3
"""Démonstration officielle du service de connaissances agricoles Backend 2 (AgriSense).

Backend 2 = QUOI CONSEILLER
Source unique et souveraine = BASE_CONNAISSANCES_AGRICOLES
"""

from __future__ import annotations

from domain.models import TreeId
from publication.releases import ReleaseManager
from repositories.cameroon import CameroonKnowledgeRepository
from repositories.rules import RuleRepository
from schemas.knowledge import KnowledgeQuery
from services.knowledge_service import KnowledgeService
from sources.catalog import DOCUMENTS, ORGANIZATIONS


def print_banner(title: str) -> None:
    print(f"\n{'=' * 75}")
    print(f"  🌱 {title}")
    print(f"{'=' * 75}")


def main() -> None:
    print_banner("AGRISENSE — BACKEND 2 : SERVICE DE CONNAISSANCES AGRICOLES (CAMEROUN)")
    print("Architecture : Autonome | Rôle : 'QUOI CONSEILLER' | Source : BASE_CONNAISSANCES_AGRICOLES\n")

    # 1. Version active et immuabilité
    release_mgr = ReleaseManager()
    active_release = release_mgr.get_active_release()
    print("📌 RELEASE OFFICIELLE ACTIVE :")
    print(f"   • Release ID     : {active_release.release_id}")
    print(f"   • Empreinte SHA256 : {active_release.sha256_hash}")
    print(f"   • Auteur         : {active_release.author}")
    print(f"   • Date           : {active_release.release_date.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"   • Sources clées  : {', '.join(active_release.sources)}")

    # 2. Catalogue documentaire
    repo = CameroonKnowledgeRepository()
    summary = repo.summary()
    print("\n📚 CONTENU DE BASE_CONNAISSANCES_AGRICOLES :")
    for key, value in summary.items():
        print(f"   • {key.replace('_', ' ').capitalize()} : {value}")

    # 3. Exploration des règles canoniques (T1 à T7)
    rule_repo = RuleRepository(repo.base)
    all_rules = rule_repo.list_rules()
    print(f"\n🌾 CATALOGUE DES RÈGLES CANONIQUES COMPILÉES ({len(all_rules)} règles) :")

    # Affichage d'un exemple pour la tomate et la pomme de terre
    for crop_name, crop_id in [("Tomate", "CULT_TOMATE"), ("Pomme de terre", "CULT_POMME_DE_TERRE")]:
        rules = rule_repo.query_rules(crop_id)
        print(f"\n   --- Culture : {crop_name} ({crop_id}) - {len(rules)} règles réparties sur T1-T7 ---")
        for r in rules[:4]:
            cond_str = ", ".join(f"{c.field} {c.operator} {c.value}" for c in r.conditions)
            print(f"   [{r.tree.value}] {r.rule_id} (Priorité: {r.priority})")
            print(f"       Condition : {cond_str}")
            print(f"       Conseil   : {r.candidate.name}")
            print(f"       Action    : {r.candidate.actions[0] if r.candidate.actions else 'N/A'}")
            print(f"       Source    : {r.source_refs[0].reference if r.source_refs else 'N/A'}")

    # 4. Simulation d'une interrogation (Knowledge Query)
    service = KnowledgeService(repository=repo, rule_repository=rule_repo, release_manager=release_mgr)
    query = KnowledgeQuery(
        crop_id="tomato",
        trees=["T1", "T2", "T4", "T5", "T7"],
        region_id="REG_OU",
        soil_id="SOL_VOLCANIQUE",
    )
    print("\n🔍 SIMULATION D'APPEL DE REQUÊTE CONTEXTUELLE (POST /api/v1/knowledge/query) :")
    print(f"   Paramètres : crop={query.crop_id}, trees={query.trees}, region={query.region_id}, soil={query.soil_id}")

    result = service.query(query)
    print(f"   ✅ Résultat : {len(result.rules)} règles éligibles, {len(result.sources)} sources identifiées.")
    for r in result.rules:
        print(f"      • [{r.tree.value}] {r.candidate.name} -> {r.candidate.summary[:80]}...")

    print_banner("DÉMONSTRATION RÉUSSIE : BACKEND 2 EST 100% OPÉRATIONNEL")


if __name__ == "__main__":
    main()

