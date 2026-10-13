from __future__ import annotations

from domain.models import SourceDocument, SourceOrganization, SourceReference

# Organismes officiels
ORGANIZATIONS: dict[str, SourceOrganization] = {
    "ORG_MINADER": SourceOrganization(
        organization_id="ORG_MINADER",
        name="Ministère de l'Agriculture et du Développement Rural du Cameroun",
        acronym="MINADER",
        country="Cameroun",
        authority_level="ministeriel_national",
        website="https://www.minader.cm",
    ),
    "ORG_IRAD": SourceOrganization(
        organization_id="ORG_IRAD",
        name="Institut de Recherche Agricole pour le Développement",
        acronym="IRAD",
        country="Cameroun",
        authority_level="recherche_nationale",
        website="https://irad.cm",
    ),
    "ORG_IFATI": SourceOrganization(
        organization_id="ORG_IFATI",
        name="Institut de Formation Agricole des Tropiques et de l'Innovation",
        acronym="IFATI",
        country="Cameroun",
        authority_level="organisme_formation_homologue",
        website="https://ifati.org",
    ),
    "ORG_FAO": SourceOrganization(
        organization_id="ORG_FAO",
        name="Organisation des Nations Unies pour l'Alimentation et l'Agriculture - Bureau Cameroun",
        acronym="FAO",
        country="International / Cameroun",
        authority_level="international",
        website="https://www.fao.org/cameroon",
    ),
    "ORG_CDE": SourceOrganization(
        organization_id="ORG_CDE",
        name="Centre pour le Développement de l'Entreprise / MINADER",
        acronym="CDE/MINADER",
        country="Cameroun",
        authority_level="programme_national",
        website=None,
    ),
    "ORG_FIBL": SourceOrganization(
        organization_id="ORG_FIBL",
        name="Institut de recherche de l'agriculture biologique (FiBL) & IFOAM Afrique",
        acronym="FiBL",
        country="International",
        authority_level="recherche_internationale",
        website="https://www.fibl.org",
    ),
}

# Documents officiels indexés
DOCUMENTS: dict[str, SourceDocument] = {
    "DOC_MINEFOP_IFATI_TOMATE": SourceDocument(
        source_id="DOC_MINEFOP_IFATI_TOMATE",
        organization_id="ORG_IFATI",
        title="Guide technique de production de la tomate au Cameroun (Arrêté Min. n° 086/MINEFOP)",
        publication_year=2018,
        document_type="guide_technique_officiel",
        canonical_url="https://minader.cm/fiches/tomate_guide_ifati.pdf",
        language="fr",
    ),
    "DOC_MINADER_CDE_PDT": SourceDocument(
        source_id="DOC_MINADER_CDE_PDT",
        organization_id="ORG_CDE",
        title="Guide pratique de la culture de la pomme de terre en Afrique de l'Ouest et du Centre (Félix Teouaba)",
        publication_year=2015,
        document_type="guide_pratique_vulgarisation",
        canonical_url="https://minader.cm/fiches/guide_pomme_de_terre_cameroun.pdf",
        language="fr",
    ),
    "DOC_IRAD_MAIS_FICHES": SourceDocument(
        source_id="DOC_IRAD_MAIS_FICHES",
        organization_id="ORG_IRAD",
        title="Itinéraire technique et variétés améliorées de maïs au Cameroun (IRAD Fiches Pôles)",
        publication_year=2020,
        document_type="fiche_technique_recherche",
        canonical_url="https://irad.cm/publications/fiches_mais_2020.pdf",
        language="fr",
    ),
    "DOC_MINADER_MANIOC_CHAIN": SourceDocument(
        source_id="DOC_MINADER_MANIOC_CHAIN",
        organization_id="ORG_MINADER",
        title="Manuel de production et de multiplication des boutures saines de manioc au Cameroun",
        publication_year=2019,
        document_type="manuel_production",
        canonical_url="https://minader.cm/fiches/manioc_itineraire.pdf",
        language="fr",
    ),
    "DOC_MINADER_PLANTAIN_PIF": SourceDocument(
        source_id="DOC_MINADER_PLANTAIN_PIF",
        organization_id="ORG_MINADER",
        title="Guide de multiplication des rejets de bananier plantain par la méthode PIF",
        publication_year=2021,
        document_type="guide_technique",
        canonical_url="https://minader.cm/fiches/plantain_pif.pdf",
        language="fr",
    ),
    "DOC_IRAD_HARICOT_HAUTS_PLATEAUX": SourceDocument(
        source_id="DOC_IRAD_HARICOT_HAUTS_PLATEAUX",
        organization_id="ORG_IRAD",
        title="Guide de conduite de la culture du haricot commun dans les hauts plateaux de l'Ouest",
        publication_year=2017,
        document_type="guide_recherche_developpement",
        canonical_url="https://irad.cm/publications/haricot_ouest.pdf",
        language="fr",
    ),
    "DOC_BASE_CANONIQUE_CM": SourceDocument(
        source_id="DOC_BASE_CANONIQUE_CM",
        organization_id="ORG_MINADER",
        title="Structure des connaissances agricoles Cameroun (Document officiel de référence)",
        publication_year=2026,
        document_type="referentiel_national",
        canonical_url="file:///backend2/Structure_des_connaissances_agricoles_Cameroun.pdf",
        language="fr",
    ),
}


def get_source_reference(source_id: str, page: str | None = None, section: str | None = None) -> SourceReference:
    doc = DOCUMENTS.get(source_id, DOCUMENTS["DOC_BASE_CANONIQUE_CM"])
    org = ORGANIZATIONS.get(doc.organization_id, ORGANIZATIONS["ORG_MINADER"])
    return SourceReference(
        source_id=doc.source_id,
        organization=f"{org.acronym} ({org.name})",
        title=doc.title,
        canonical_url=doc.canonical_url,
        document_type=doc.document_type,
        page=page,
        section=section,
        reference=f"{org.acronym} - {doc.title}" + (f", p. {page}" if page else ""),
        publication_date=str(doc.publication_year) if doc.publication_year else None,
        authority_level=doc.authority_level,
    )

