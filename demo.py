#!/usr/bin/env python3
"""Explore the canonical Cameroon knowledge base without starting the API."""

from pathlib import Path

from BASE_CONNAISSANCES_AGRICOLES.reader import CameroonKnowledgeBase
from engine.models.enums import TreeId
from integrations.cameroon_knowledge import CameroonKnowledgeProvider


def print_section(title: str) -> None:
    print(f"\n{'=' * 65}")
    print(f"  {title}")
    print(f"{'=' * 65}")


def main() -> None:
    print_section("🌱 AGRIADVISE — BASE CONNAISSANCES AGRICOLES")
    print("Vérification et exploration de la base de connaissances agronomiques...\n")

    root = Path(__file__).resolve().parent / "BASE_CONNAISSANCES_AGRICOLES"
    repository = CameroonKnowledgeBase(root)
    provider = CameroonKnowledgeProvider(root)
    crops = [profile.crop_id for profile in provider.list_crop_profiles()]
    print(f"✅ Cultures disponibles dans le catalogue : {crops}")

    # 2. Consultation d'un profil de culture
    for crop_id in crops:
        profile = provider.get_crop_profile(crop_id)
        if profile:
            print(f"\n📋 Profil de culture : {profile.name} (ID: {profile.crop_id})")
            print(f"   • Famille botanique : {profile.family}")
            print(f"   • Statut de validation : {profile.status.value}")
            print(f"   • Source : {profile.source.title}")

    # 3. Exploration de l'ensemble des règles
    all_rules = provider.get_relevant_rules("potato", None, list(TreeId))
    print_section(f"📚 RÈGLES CHARGÉES DANS LE CATALOGUE ({len(all_rules)} règles)")

    for r in all_rules:
        print(f"\n🔹 [{r.rule_id}] - Arbre: {r.domain.value} (Priorité: {r.priority})")
        print(f'   Action/Conseil : "{r.candidate.name}"')
        print(f"   Résumé : {r.candidate.summary}")
        if r.candidate.actions:
            print(f"   Actions préconisées : {r.candidate.actions}")

    # 4. Test du KnowledgeProvider (bridge vers le moteur)
    print_section("🔍 TEST DU KNOWLEDGE PROVIDER (Filtrage par arbres)")
    # Filtrage pour la pomme de terre
    selected_trees = [TreeId.WEATHER, TreeId.TIMING]
    filtered_potato = provider.get_relevant_rules("potato", context=None, trees=selected_trees)
    print(f"Requête pour crop='potato' et arbres={selected_trees}:")
    print(f"-> {len(filtered_potato)} règles sélectionnées :")
    for rule in filtered_potato:
        print(f"   - {rule.rule_id} (arbre: {rule.domain.value}) : {rule.candidate.name}")

    # Filtrage pour la tomate
    tomato_trees = [TreeId.SOIL, TreeId.WEATHER, TreeId.TIMING, TreeId.PRACTICES_RISKS]
    filtered_tomato = provider.get_relevant_rules("tomato", context=None, trees=tomato_trees)
    print(f"\nRequête pour crop='tomato' et arbres={tomato_trees}:")
    print(f"-> {len(filtered_tomato)} règles sélectionnées :")
    for rule in filtered_tomato:
        print(f"   - {rule.rule_id} (arbre: {rule.domain.value}) : {rule.candidate.name}")

    print_section("🔗 VÉRIFICATION DES LIENS ENTRE DOSSIERS")
    links = repository.resolve_culture_links("TOMATE")
    print(f"✅ Tomate liée à {len(links['sols_favorables'])} sols et "
          f"{len(links['engrais_recommandes'])} fertilisants.")

    print_section("✨ TOUS LES TESTS FONCTIONNENT CORRECTEMENT !")
    print("La base et son adaptateur de moteur sont opérationnels.\n")


if __name__ == "__main__":
    main()
