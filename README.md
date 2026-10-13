# AgriSense Backend 2 — Cameroon Agricultural Knowledge Service

Service autonome et souverain de connaissances agricoles du Cameroun (**« QUOI CONSEILLER »**).

```text
Backend 1 (Raisonnement)  : COMMENT conseiller (Moteur décisionnel)
Backend de liaison        : TRADUCTION & TRANSPORT (Adaptateur de contrats)
Backend 2 (Connaissances) : QUOI conseiller (Base canonique & Règles agronomiques)
```

---

## 1. Règle Fondamentale : Source Unique et Canonique

La seule source canonique de toute connaissance agricole dans AgriSense est :
```text
BASE_CONNAISSANCES_AGRICOLES/
```
- **72 fichiers JSON officiels** conformes à `Structure_des_connaissances_agricoles_Cameroun.pdf`.
- **6 cultures camerounaises documentées** : Tomate, Pomme de terre, Maïs, Haricot commun, Manioc, Bananier plantain.
- **7 familles botaniques**.
- **10 régions administratives (10/10) & 12 localités / bassins**.
- **6 types de sols majeurs** (Andosols, Vertisols, etc.) avec matrice d'adéquation.
- **4 calendriers culturaux régionaux**.
- **14 modules de fertilisation, risques, ravageurs et bonnes pratiques**.

L'ancien dossier prototype `knowledge/` et le moteur `engine/` ont été totalement retirés. Backend 2 est **100% autonome** et n'importe aucun composant de Backend 1.

---

## 2. Architecture Arbres T1 à T7 & Règles Canoniques

Backend 2 compile et expose **42 règles agronomiques canoniques** couvrant les 6 cultures et les 7 arbres décisionnels :
- **T1 : Profil de Culture** (`RULE_<CROP>_T1_PROFILE_001`)
- **T2 : Aptitude du Sol et Amélioration** (`RULE_<CROP>_T2_SOIL_001` : acidité, dolomie si pH < 5.5, fumure organique)
- **T3 : Contexte Régional et Bassins** (`RULE_<CROP>_T3_REGION_001` : adaptation aux régions agroécologiques)
- **T4 : Topographie et Pente** (`RULE_<CROP>_T4_TOPO_001` : courbes de niveau, buttage anti-érosif, vétiver)
- **T5 : Climat et Vigilance Météo** (`RULE_<CROP>_T5_CLIMATE_001` : alerte mildiou après 3 jours de fortes pluies)
- **T6 : Calendrier et Fenêtres de Plantation** (`RULE_<CROP>_T6_TIMING_001` : confirmation d'installation des pluies)
- **T7 : Pratiques, Rotation et Protection** (`RULE_<CROP>_T7_PRACTICES_001` : rotation 3-4 ans hors solanacées, tuteurage)

Chaque règle est reliée à ses documents sources officiels (MINADER, IRAD, IFATI, FAO, CDE).

---

## 3. Contrat d'API REST

Backend 2 est servi par FastAPI sur le port 8000 :

| Méthode | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Statut de santé et scope du service |
| `GET` | `/api/v1/knowledge/version` | Release active, empreinte SHA-256, statistiques |
| `GET` | `/api/v1/crops` | Liste des 6 cultures camerounaises |
| `GET` | `/api/v1/crops/{crop_id}` | Détail d'une culture (accepte code ou alias) |
| `GET` | `/api/v1/regions` | Liste des 10 régions du Cameroun |
| `GET` | `/api/v1/regions/{region_id}` | Détail d'une région administrative et ses localités |
| `GET` | `/api/v1/soils` | Liste des types de sols |
| `GET` | `/api/v1/soils/{soil_id}` | Profil pédologique et matrice d'adéquation |
| `GET` | `/api/v1/rules` | Catalogue complet des 42 règles canoniques |
| `GET` | `/api/v1/rules/{rule_id}` | Détail d'une règle spécifique |
| `GET` | `/api/v1/sources` | Catalogue des documents sources officiels |
| `GET` | `/api/v1/sources/{source_id}` | Métadonnées d'un document source |
| `GET` | `/api/v1/knowledge/items/{id}` | Recherche universelle d'un item de connaissance |
| `POST` | `/api/v1/knowledge/query` | Requête contextuelle (retourne règles et sources éligibles) |

### Exemple de Requête Contextuelle
```bash
curl -X POST http://localhost:8000/api/v1/knowledge/query \
  -H "Content-Type: application/json" \
  -d '{
    "crop_id": "tomato",
    "trees": ["T1", "T2", "T4", "T5", "T7"],
    "region_id": "REG_OU",
    "soil_id": "SOL_VOLCANIQUE"
  }'
```

*Règle d'or : Backend 2 fournit les connaissances brutes et éligibles. Il n'effectue aucun calcul de score final et ne filtre aucune recommandation gagnante.*

---

## 4. Validation Stricte et Tests

```bash
# 1. Validation stricte de l'intégralité de BASE_CONNAISSANCES_AGRICOLES (0 erreur tolérée)
python3 -m scripts.validate_knowledge

# 2. Exécution de la suite complète de 33 tests automatisés
pytest tests

# 3. Démonstration interactive du service
python3 demo.py
```

---

## 5. Provenance, Staging et Releases Immuables

- **Sources officielles indexées :** MINADER, IRAD, IFATI, FAO, CDE, FiBL.
- **Pipeline d'ingestion Web (Sources futures) :**
  ```text
  DISCOVER -> FETCH -> SNAPSHOT -> EXTRACT -> NORMALIZE -> COMPARE -> STAGE -> HUMAN REVIEW -> VALIDATE -> RELEASE -> PUBLISH
  ```
- **Sécurité :** Aucune donnée issue d'Internet ne modifie directement `BASE_CONNAISSANCES_AGRICOLES`. Toutes les propositions transitent par `ingestion/staging/` et font l'objet d'une fiche de revue humaine (`ValidationReview`) avec détection de conflit.
- **Releases immuables :** Chaque version publiée (ex: `CM-KNOWLEDGE-2026.10.1`) possède une empreinte cryptographique SHA-256 déterministe.
- **Persistance :** Support relationnel PostgreSQL avec export/import JSON déterministe (`persistence/`).
