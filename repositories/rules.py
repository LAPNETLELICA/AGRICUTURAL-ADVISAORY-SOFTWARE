"""Repository canonique des règles agricoles compilées exclusivement depuis BASE_CONNAISSANCES_AGRICOLES."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from BASE_CONNAISSANCES_AGRICOLES.reader import CameroonKnowledgeBase
from domain.aliases import normalize_crop_id, normalize_region_id, normalize_soil_id
from domain.models import (
    AgriculturalRule,
    CandidateRecommendation,
    ConditionSpec,
    KnowledgeStatus,
    SourceReference,
    TreeId,
)
from sources.catalog import get_source_reference


class RuleRepository:
    """Fournit les règles agricoles canoniques structurées par arbres décisionnels T1-T7."""

    def __init__(self, base: CameroonKnowledgeBase | None = None) -> None:
        self.base = base or CameroonKnowledgeBase()
        self._rules: dict[str, AgriculturalRule] = {}
        self._compiled = False
        self._compile_all_rules()

    def _compile_all_rules(self) -> None:
        if self._compiled:
            return

        cultures = self.base.list_cultures()
        for cult in cultures:
            crop_code = cult.get("code", "")
            if not crop_code:
                continue

            links = cult.get("liens_dossiers", {})
            nom_courant = cult.get("nom_courant", crop_code)
            cycle = cult.get("cycle_jours", {})
            besoins = cult.get("besoins", {})

            # Source par défaut selon la culture
            source_map = {
                "CULT_TOMATE": ("DOC_MINEFOP_IFATI_TOMATE", "12-18", "Guide IFATI"),
                "CULT_POMME_DE_TERRE": ("DOC_MINADER_CDE_PDT", "24-30", "Guide CDE/MINADER"),
                "CULT_MAIS": ("DOC_IRAD_MAIS_FICHES", "4-8", "Fiches IRAD Maïs"),
                "CULT_HARICOT": ("DOC_IRAD_HARICOT_HAUTS_PLATEAUX", "6-10", "Guide IRAD Haricot"),
                "CULT_MANIOC": ("DOC_MINADER_MANIOC_CHAIN", "15-20", "Manuel MINADER Manioc"),
                "CULT_BANANIER_PLANTAIN": ("DOC_MINADER_PLANTAIN_PIF", "8-14", "Guide PIF MINADER"),
            }
            src_id, src_page, src_sec = source_map.get(
                crop_code, ("DOC_BASE_CANONIQUE_CM", "1", "Référentiel National")
            )
            primary_source = get_source_reference(src_id, page=src_page, section=src_sec)

            # ---------------------------------------------------------
            # T1 : Profil de culture
            # ---------------------------------------------------------
            rule_t1_id = f"RULE_{crop_code}_T1_PROFILE_001"
            self._rules[rule_t1_id] = AgriculturalRule(
                rule_id=rule_t1_id,
                crop_id=crop_code,
                tree=TreeId.T1_PROFILE,
                domain="Profil de culture",
                version="1.0.0",
                priority=100,
                status=KnowledgeStatus.PUBLISHED,
                conditions=[
                    ConditionSpec(field="crop.is_active", operator="eq", value=True)
                ],
                candidate=CandidateRecommendation(
                    candidate_id=f"CAND_{crop_code}_PROFILE",
                    type="advisory",
                    name=f"Profil agronomique : {nom_courant}",
                    summary=f"Cycle optimal de {cycle.get('optimal', 90)} jours. Besoins thermiques : {besoins.get('temperature_optimale', 'optimal')}.",
                    actions=[
                        f"Respecter la période de cycle recommandée ({cycle.get('optimal', 90)} jours)",
                        f"Veiller au respect des températures idéales ({besoins.get('temperature_optimale', '20-25°C')})",
                    ],
                    reasons=[
                        f"Le respect du cycle végétatif garantit l'expression du potentiel génétique de {nom_courant}."
                    ],
                ),
                source_refs=[primary_source],
            )

            # ---------------------------------------------------------
            # T2 : Aptitude du sol & Amélioration
            # ---------------------------------------------------------
            sols_fav = self.base.get_sols_favorables(crop_code)
            soil_codes = [s.get("code") for s in sols_fav if s.get("code")]
            rule_t2_id = f"RULE_{crop_code}_T2_SOIL_001"
            self._rules[rule_t2_id] = AgriculturalRule(
                rule_id=rule_t2_id,
                crop_id=crop_code,
                tree=TreeId.T2_SOIL,
                domain="Aptitude du sol et fertilisation de fond",
                version="1.0.0",
                priority=120,
                status=KnowledgeStatus.PUBLISHED,
                soil_ids=soil_codes,
                conditions=[
                    ConditionSpec(field="soil.ph", operator="lt", value=5.5)
                ],
                candidate=CandidateRecommendation(
                    candidate_id=f"CAND_{crop_code}_SOIL_AMENDMENT",
                    type="soil_action",
                    name=f"Correction de l'acidité et amélioration du sol pour {nom_courant}",
                    summary="Sur sol acide (pH < 5.5), réaliser un amendement calcaire (dolomie) associé à un apport massif de fumure organique.",
                    actions=[
                        "Apporter 150 à 250 g/m² de dolomie ou chaux agricole au moins 3 semaines avant plantation",
                        "Enfouir 20 à 30 tonnes/ha de compost bien décomposé ou fumier mûr",
                        "Éviter les sols hydromorphes mal drainés provoquant l'asphyxie racinaire",
                    ],
                    warnings=[
                        "Ne jamais mélanger directement la chaux avec un engrais azoté minéral."
                    ],
                    reasons=[
                        "Un pH inférieur à 5.5 bloque l'assimilation du phosphore et favorise la toxicité aluminique."
                    ],
                ),
                source_refs=[primary_source],
            )

            # ---------------------------------------------------------
            # T3 : Contexte Régional
            # ---------------------------------------------------------
            region_codes = links.get("regions_principales", [])
            rule_t3_id = f"RULE_{crop_code}_T3_REGION_001"
            self._rules[rule_t3_id] = AgriculturalRule(
                rule_id=rule_t3_id,
                crop_id=crop_code,
                tree=TreeId.T3_REGION,
                domain="Adaptation régionale",
                version="1.0.0",
                priority=90,
                status=KnowledgeStatus.PUBLISHED,
                region_ids=region_codes,
                conditions=[
                    ConditionSpec(field="location.region", operator="in", value=region_codes)
                ],
                candidate=CandidateRecommendation(
                    candidate_id=f"CAND_{crop_code}_REGION_FIT",
                    type="advisory",
                    name=f"Validation du bassin agroécologique pour {nom_courant}",
                    summary=f"Culture adaptée aux bassins prioritaires camerounais : {', '.join(region_codes)}.",
                    actions=[
                        "Choisir les variétés homologuées adaptées au bassin régional",
                        "Consulter les services locaux du MINADER pour l'approvisionnement en semences certifiées",
                    ],
                    reasons=[
                        f"Les conditions bioclimatiques des régions {region_codes} assurent une productivité optimale."
                    ],
                ),
                source_refs=[primary_source],
            )

            # ---------------------------------------------------------
            # T4 : Topographie et Pente
            # ---------------------------------------------------------
            rule_t4_id = f"RULE_{crop_code}_T4_TOPO_001"
            self._rules[rule_t4_id] = AgriculturalRule(
                rule_id=rule_t4_id,
                crop_id=crop_code,
                tree=TreeId.T4_TOPOGRAPHY,
                domain="Aménagement topographique anti-érosif",
                version="1.0.0",
                priority=110,
                status=KnowledgeStatus.PUBLISHED,
                conditions=[
                    ConditionSpec(field="topography.slope", operator="in", value=["medium", "steep", "forte"])
                ],
                candidate=CandidateRecommendation(
                    candidate_id=f"CAND_{crop_code}_SLOPE_MGMT",
                    type="practice",
                    name=f"Aménagement anti-érosif sur parcelle en pente ({nom_courant})",
                    summary="Sur terrain en pente, confectionner impérativement les billons ou buttes perpendiculairement à la pente selon les courbes de niveau.",
                    actions=[
                        "Tracer les billons perpendiculairement à la pente en suivant les courbes de niveau",
                        "Installer des bandes d'arrêt herbeuses (vétiver) ou cordons pierreux en amont",
                        "Pailler le sol pour limiter la force d'impact des gouttes de pluie et le ravinement",
                    ],
                    warnings=[
                        "Ne jamais orienter les billons dans le sens de la plus grande pente sous peine de lessivage total."
                    ],
                    reasons=[
                        "L'érosion emporte la terre arable fertile et déchausse les plants ou tubercules."
                    ],
                ),
                source_refs=[primary_source],
            )

            # ---------------------------------------------------------
            # T5 : Climat et Risque Fortes Pluies
            # ---------------------------------------------------------
            rule_t5_id = f"RULE_{crop_code}_T5_CLIMATE_001"
            self._rules[rule_t5_id] = AgriculturalRule(
                rule_id=rule_t5_id,
                crop_id=crop_code,
                tree=TreeId.T5_CLIMATE,
                domain="Vigilance climatique et phytosanitaire",
                version="1.0.0",
                priority=130,
                status=KnowledgeStatus.PUBLISHED,
                conditions=[
                    ConditionSpec(field="weather.consecutive_rain_days", operator="gte", value=3)
                ],
                candidate=CandidateRecommendation(
                    candidate_id=f"CAND_{crop_code}_RAIN_ALERT",
                    type="risk_alert",
                    name=f"Vigilance maladies foliaires et mildiou en période de fortes pluies ({nom_courant})",
                    summary="Après 3 jours consécutifs de pluie ou en humidité relative > 85%, intensifier la surveillance phytosanitaire.",
                    actions=[
                        "Inspecter quotidiennement la face inférieure des feuilles à la recherche de taches suspectes",
                        "Éliminer immédiatement et brûler les parties végétales contaminées",
                        "Appliquer un traitement fongicide préventif homologué dès la première éclaircie",
                    ],
                    warnings=[
                        "Ne jamais traiter en plein soleil ou sous la pluie battante."
                    ],
                    reasons=[
                        "L'humidité saturante et les températures douces créent un terrain favorable à la germination des spores fongiques."
                    ],
                ),
                source_refs=[primary_source],
            )

            # ---------------------------------------------------------
            # T6 : Calendrier et Fenêtre de plantation
            # ---------------------------------------------------------
            rule_t6_id = f"RULE_{crop_code}_T6_TIMING_001"
            self._rules[rule_t6_id] = AgriculturalRule(
                rule_id=rule_t6_id,
                crop_id=crop_code,
                tree=TreeId.T6_TIMING,
                domain="Calendrier et déclenchement des semis",
                version="1.0.0",
                priority=105,
                status=KnowledgeStatus.PUBLISHED,
                conditions=[
                    ConditionSpec(field="weather.rain_confirmed", operator="eq", value=True)
                ],
                candidate=CandidateRecommendation(
                    candidate_id=f"CAND_{crop_code}_TIMING_CONFIRM",
                    type="timing",
                    name=f"Confirmation de la fenêtre de plantation ({nom_courant})",
                    summary="La mise en place en plein champ ne doit intervenir qu'après confirmation de l'installation effective de la saison des pluies.",
                    actions=[
                        "Vérifier le calendrier cultural régional officiel (calendrier Ouest, Centre-Sud ou Grand Nord)",
                        "Repiquer ou semer en fin d'après-midi ou par temps couvert",
                        "Arroser abondamment les planches de pépinière 2 heures avant arrachage",
                    ],
                    warnings=[
                        "Ne pas semer sur un sol sec en se basant sur une seule pluie isolée."
                    ],
                    reasons=[
                        "Un arrêt brutal des pluies après semis entraîne une perte de levée irrémédiable."
                    ],
                ),
                source_refs=[primary_source],
            )

            # ---------------------------------------------------------
            # T7 : Pratiques, Rotation et Protection
            # ---------------------------------------------------------
            rule_t7_id = f"RULE_{crop_code}_T7_PRACTICES_001"
            self._rules[rule_t7_id] = AgriculturalRule(
                rule_id=rule_t7_id,
                crop_id=crop_code,
                tree=TreeId.T7_PRACTICES,
                domain="Bonnes pratiques culturales et rotation",
                version="1.0.0",
                priority=115,
                status=KnowledgeStatus.PUBLISHED,
                conditions=[
                    ConditionSpec(field="practices.crop_rotation_years", operator="lt", value=3)
                ],
                candidate=CandidateRecommendation(
                    candidate_id=f"CAND_{crop_code}_ROTATION_PRACTICE",
                    type="practice",
                    name=f"Rotation culturale et entretien intégré pour {nom_courant}",
                    summary="Observer un délai minimal de 3 à 4 ans avant de replanter la même famille botanique sur la même parcelle. Pratiquer le tuteurage et paillage.",
                    actions=[
                        "Alterner avec une légumineuse fixatrice d'azote (haricot, soja) ou une graminée (maïs)",
                        "Tuteurer solidement les tiges pour aérer le feuillage et éloigner les fruits du sol humide",
                        "Effectuer les sarclages et binages réguliers dès l'apparition des adventices",
                    ],
                    warnings=[
                        "Ne jamais faire succéder deux cultures de la même famille (ex: tomate après pomme de terre ou piment)."
                    ],
                    reasons=[
                        "La monoculture concentre les nématodes et champignons telluriques dans l'horizon racinaire."
                    ],
                ),
                source_refs=[primary_source],
            )

        self._compiled = True

    def list_rules(self) -> list[AgriculturalRule]:
        return list(self._rules.values())

    def get_rule(self, rule_id: str) -> AgriculturalRule | None:
        return self._rules.get(rule_id.strip())

    def query_rules(
        self,
        crop_id: str,
        trees: list[TreeId] | list[str] | None = None,
        region_id: str | None = None,
        soil_id: str | None = None,
    ) -> list[AgriculturalRule]:
        canonical_crop = normalize_crop_id(crop_id)
        selected_tree_values = {
            t.value if isinstance(t, TreeId) else str(t).upper()
            for t in (trees or list(TreeId))
        }

        canonical_region = normalize_region_id(region_id) if region_id else None
        canonical_soil = normalize_soil_id(soil_id) if soil_id else None

        matched: list[AgriculturalRule] = []
        for rule in self._rules.values():
            if rule.crop_id != canonical_crop:
                continue
            if rule.tree.value not in selected_tree_values:
                continue

            # Filtrage contextuel souple
            if canonical_region and rule.region_ids and canonical_region not in rule.region_ids:
                continue
            if canonical_soil and rule.soil_ids and canonical_soil not in rule.soil_ids:
                continue

            matched.append(rule)

        # Tri déterministe par Arbre (T1..T7) puis Priorité décroissante
        tree_order = [t.value for t in TreeId]
        matched.sort(
            key=lambda r: (
                tree_order.index(r.tree.value) if r.tree.value in tree_order else 99,
                -r.priority,
                r.rule_id,
            )
        )
        return matched

