# Base de Connaissances Agricoles du Cameroun (BASE_CONNAISSANCES_AGRICOLES)

Cette base documentaire structurée implémente les spécifications du document **`Structure_des_connaissances_agricoles_Cameroun.pdf`** situé à la racine du backend. Elle a pour but de fournir une base de connaissances propre, détaillée, exploitable et adaptée au contexte agro-écologique du Cameroun.

---

## 1. Principes Directeurs et Séparation des Dossiers

Conformément à la spécification :
1. **Principe de séparation stricte** : Chaque connaissance est rangée dans son dossier thématique propre afin d'éliminer les doublons.
2. **Interconnexions par codes stables** : Les fiches ne dupliquent pas les informations d'un autre domaine, mais s'y réfèrent par des identifiants universels stables (ex: `CULT_TOMATE` réfère à `SOL_VOLCANIQUE`, `REG_OU`, `CLIM_ZONE_III`, `ENG_NPK_12_14_19`, etc.).
3. **Isolement des maladies des plantes** : Le dossier `MALADIES_DES_PLANTES` est séparé de `RISQUES_ET_PRATIQUES` pour être enrichi dans une phase ultérieure.
4. **Indépendance du moteur de décision** : La base stocke le savoir agronomique factuel camerounais. Les moteurs d'inférence et d'évaluation viennent exploiter cette base sans en dénaturer le contenu.

---

## 2. Arborescence de la Base

```text
BASE_CONNAISSANCES_AGRICOLES/
├── CODIFICATION.json                        # Registre universel des codes et préfixes
├── README.md                                # Guide d'architecture et gouvernance (ce fichier)
├── reader.py                                # API Python d'interrogation et navigation
│
├── CULTURE/
│   ├── FAMILLES/                            # Grandes familles agricoles camerounaises
│   ├── CULTURES/                            # Fiches cultures (nom scientifique, cycle, tolérances, liens)
│   └── VARIETES/                            # Variétés vulgarisées et cultivées au Cameroun
│
├── SOL/
│   ├── TYPES_SOL/                           # Typologie pédologique camerounaise (volcaniques, ferrallitiques, etc.)
│   ├── CARACTERISTIQUES/                    # Propriétés physiques (texture/structure) et chimiques (pH/NPK)
│   ├── SOL_PAR_CULTURE/                     # Matrice d'adéquation sol-plante (favorable/défavorable)
│   ├── SOL_PAR_REGION/                      # Répartition régionale des sols au Cameroun
│   └── ENTRETIEN_RESTAURATION/              # Chaulage, gestion MO, lutte anti-érosive
│
├── REGION/
│   ├── 10_REGIONS/                          # Les 10 régions administratives du Cameroun
│   └── LOCALITES/                           # Départements, villes et bassins de production
│
├── CLIMAT/                                  # 5 zones agro-écologiques, pluviométrie, températures
│
├── CALENDRIER_CULTURAL/                     # Calendriers des opérations culturales par zone et culture
│
├── RISQUES_ET_PRATIQUES/
│   ├── BONNES_PRATIQUES/                    # Préparation sol, tuteurage, rotation, paillage
│   ├── ENGRAIS_ET_FERTILISATION/            # Engrais minéraux homologués et fertilisants organiques locaux
│   ├── RAVAGEURS_ET_PESTES/                 # Ravageurs majeurs au Cameroun (Tuta, noctuelles, etc.)
│   ├── RISQUES_AGRICOLES/                   # Sécheresse, engorgement, érosion, dégradation
│   └── RESTAURATION_REPOS_ROTATION/         # Jachères améliorées, assolements protecteurs
│
├── TOPOGRAPHIE/                             # Reliefs, altitudes, pentes et aménagements anti-érosifs
│
├── PHOTOS/                                  # Référentiel des ressources visuelles et métadonnées associées
│
└── MALADIES_DES_PLANTES/                    # Espace réservé pour la phase ultérieure
```

---

## 3. Matrice des Relations Inter-Dossiers

| Relation | Dossier Source | Dossier Cible | Mécanisme de Lien |
| --- | --- | --- | --- |
| **Culture ↔ Sol** | `CULTURE/CULTURES` | `SOL/TYPES_SOL` | Code `sols_favorables`, `sols_defavorables` |
| **Culture ↔ Région** | `CULTURE/CULTURES` | `REGION/10_REGIONS` | Code `regions_principales` (ex: `REG_OU`, `REG_NW`) |
| **Culture ↔ Climat** | `CULTURE/CULTURES` | `CLIMAT` | Code `zones_climatiques_favorables` (ex: `CLIM_ZONE_III`) |
| **Culture ↔ Calendrier** | `CULTURE/CULTURES` | `CALENDRIER_CULTURAL` | Identifiants `calendrier_ref` par région |
| **Culture ↔ Pratiques/Engrais** | `CULTURE/CULTURES` | `RISQUES_ET_PRATIQUES` | Codes `pratiques_cles`, `engrais_recommandes` |
| **Région ↔ Sol** | `REGION/10_REGIONS` | `SOL/TYPES_SOL` | Codes `sols_dominants` |
| **Région ↔ Climat** | `REGION/10_REGIONS` | `CLIMAT` | Code `zone_agroecologique` |
| **Région ↔ Topographie** | `REGION/10_REGIONS` | `TOPOGRAPHIE` | Code `profil_topographique` |
| **Sol ↔ Bonnes pratiques** | `SOL/TYPES_SOL` | `RISQUES_ET_PRATIQUES/BONNES_PRATIQUES` | Recommandations d'amendement et travail |
| **Photos ↔ Fiches** | `PHOTOS/metadata_catalogue.json` | Tous dossiers | Attribut `entite_associee_code` |

---

## 4. Traçabilité des Sources Agronomiques

Toutes les connaissances intégrées s'appuient sur des références techniques reconnues au Cameroun :
- **Guide technique IFATI** (Institut de Formation Agricole de Tiko, Arrêté Min. n° 086/MINEFOP Cameroun)
- **Fiches techniques IRAD** (Institut de Recherche Agricole pour le Développement, Cameroun)
- **Guide pratique de la culture de la pomme de terre en Afrique de l'Ouest et du Centre** (CDE / MINADER Cameroun, Félix Teouaba)
- **SDRdag 2016** (Service de Développement Rural et de l'Agriculture)
- **Manuel de formation en agriculture biologique pour l'Afrique** (FiBL / IFOAM)
