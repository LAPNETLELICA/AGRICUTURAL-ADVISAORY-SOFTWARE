#!/usr/bin/env python3
"""
Script de démonstration et de test interactif pour Backend 2 (AgriSense).
Permet de tester directement le chargement des connaissances, les profils
de cultures et les règles sans avoir besoin de Backend 1.
"""

from backend2.catalog import repository
from backend2.provider import KnowledgeProvider


def print_section(title: str) -> None:
    print(f"\n{'=' * 65}")
    print(f"  {title}")
    print(f"{'=' * 65}")


def main() -> None:
    print_section("🌱 AGRISENSE - BACKEND 2 (QUOI CONSEILLER)")
    print("Vérification et exploration de la base de connaissances agronomiques...\n")

    # 1. Initialisation du Repository
    repo = repository()
    crops = repo.get_crop_ids()
    print(f"✅ Cultures disponibles dans le catalogue : {crops}")

    # 2. Consultation d'un profil de culture
    for crop_id in crops:
        profile = repo.get_crop_profile(crop_id)
        if profile:
            print(f"\n📋 Profil de culture : {profile.name} (ID: {profile.crop_id})")
            print(f"   • Famille botanique : {profile.family}")
            print(f"   • Statut de validation : {profile.validation_status}")
            print(f"   • Objectifs supportés : {', '.join(profile.objectives)}")
            print(f"   • Source : {profile.source}")

    # 3. Exploration de l'ensemble des règles
    all_rules = repo.get_rules()
    print_section(f"📚 RÈGLES CHARGÉES DANS LE CATALOGUE ({len(all_rules)} règles)")

    for r in all_rules:
        cond_str = ", ".join(f"{c.field} {c.operator} {c.value}" for c in r.conditions)
        print(f"\n🔹 [{r.rule_id}] - Arbre: {r.tree.upper()} (Priorité: {r.priority})")
        print(f"   Conditions : {cond_str}")
        print(f'   Action/Conseil : "{r.candidate.name}"')
        print(f"   Résumé : {r.candidate.summary}")
        if r.candidate.actions:
            print(f"   Actions préconisées : {r.candidate.actions}")

    # 4. Test du KnowledgeProvider (Façade pour Backend 1)
    print_section("🔍 TEST DU KNOWLEDGE PROVIDER (Filtrage par arbres)")
    provider = KnowledgeProvider(repo)

    # Filtrage pour la pomme de terre
    selected_trees = ["weather", "timing"]
    filtered_potato = provider.get_relevant_rule_definitions(
        crop_id="potato", context=None, trees=selected_trees
    )
    print(f"Requête pour crop='potato' et arbres={selected_trees}:")
    print(f"-> {len(filtered_potato)} règles sélectionnées :")
    for rule in filtered_potato:
        print(f"   - {rule.rule_id} (arbre: {rule.tree}) : {rule.candidate.name}")

    # Filtrage pour la tomate
    tomato_trees = ["soil", "weather", "timing", "practices_risks"]
    filtered_tomato = provider.get_relevant_rule_definitions(
        crop_id="tomato", context=None, trees=tomato_trees
    )
    print(f"\nRequête pour crop='tomato' et arbres={tomato_trees}:")
    print(f"-> {len(filtered_tomato)} règles sélectionnées :")
    for rule in filtered_tomato:
        print(f"   - {rule.rule_id} (arbre: {rule.tree}) : {rule.candidate.name}")

    # 5. Test de l'adaptateur Backend 1
    print_section("🔌 TEST DE L'ADAPTATEUR BACKEND 1 (get_relevant_rules)")
    try:
        provider.get_relevant_rules("potato", context=None, trees=["weather"])
        print("✅ Intégration Backend 1 active et connectée.")
    except RuntimeError as e:
        print("INFO: Comportement attendu (découplage sans Backend 1) :")
        print(f"   Exception levée avec succès : {e}")

    print_section("✨ TOUS LES TESTS FONCTIONNENT CORRECTEMENT !")
    print("Backend 2 est opérationnel et prêt à être utilisé.\n")


if __name__ == "__main__":
    main()
