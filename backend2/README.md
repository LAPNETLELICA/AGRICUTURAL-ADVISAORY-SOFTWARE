# Agricultural Advisory Software — Backend 2 (AgriSense)

Backend 2 incarne la responsabilité **« QUOI CONSEILLER »** dans l'architecture v3.0 du système consultatif agricole centré sur la culture.

Ce composant gère l'ensemble de la forêt de connaissances agronomiques organisée selon les 7 arbres de décision :
- **T1** : Profil de culture (racine) — *Crop Profile*
- **T2** : Aptitude et amélioration du sol — *Soil*
- **T3** : Contexte régional et qualification de risque — *Regional*
- **T4** : Topographie et altitude — *Topography*
- **T5** : Conditions météo et climat — *Weather / Climate*
- **T6** : Calendrier et fenêtres de plantation — *Timing*
- **T7** : Pratiques culturales, rotation et gestion des risques — *Practices / Risks*

Toute la logique agronomique est strictement **déclarative** (fichiers JSON) : aucun seuil ni règle n'est codé en dur dans le code Python.

---

## 🚀 Guide de Démarrage & Tests Rapides

Backend 2 utilise **exclusivement la bibliothèque standard de Python** (aucun `pip install` requis pour le fonctionnement de base).

### Option 1 : Lancer la Démonstration Complète (Clé en main)

Un script interactif permet de charger et tester tous les composants d'un seul coup :

```bash
cd /home/skyfall/Documents/KA-DIS/projet/agrisense/backend2
python3 demo.py
```

Ce script affiche :
1. La liste des cultures chargées (`potato`).
2. Le profil agronomique détaillé de la culture.
3. L'intégralité des règles déclaratives actives (conditions, actions préconisées, priorités).
4. Un exemple de filtrage par arbres de décision via le `KnowledgeProvider`.
5. Le statut du lien d'intégration avec Backend 1.

---

### Option 2 : Exécuter la Suite de Tests Automatisés (`pytest`)

Pour exécuter l'ensemble des tests unitaires validant le repository et le provider :

```bash
cd /home/skyfall/Documents/KA-DIS/projet/agrisense/backend2
PYTHONPATH=. python3 -m pytest tests -v
```

> **Résultat attendu :** Les 6 tests (`tests/test_repository.py` et `tests/test_provider.py`) doivent être au vert (`PASSED`).

---

### Option 3 : Tester Interactivement dans Python (REPL)

Vous pouvez tester manuellement le code dans une console interactive Python :

```python
# Lancez python3 depuis le dossier backend2 (avec PYTHONPATH=.)
from backend2.catalog import repository
from backend2.provider import KnowledgeProvider

# 1. Initialiser le repository
repo = repository()

# 2. Lister les cultures disponibles
print(repo.get_crop_ids())
# Output: ['potato']

# 3. Récupérer le profil d'une culture
profile = repo.get_crop_profile("potato")
print(f"Culture: {profile.name}, Famille: {profile.family}")
# Output: Culture: Pomme de terre, Famille: Solanaceae

# 4. Récupérer toutes les règles agronomiques
rules = repo.get_rules()
print(f"Nombre de règles chargées : {len(rules)}")

# 5. Utiliser le KnowledgeProvider pour filtrer par arbres de décision
provider = KnowledgeProvider(repo)
relevant = provider.get_relevant_rule_definitions(
    "potato", context=None, trees=["weather", "timing"]
)
for r in relevant:
    print(f"- {r.rule_id} [{r.tree}]: {r.candidate.name}")
```

---

## 📁 Organisation du Répertoire

```text
backend2/
├── demo.py                       # Script d'exécution et de démonstration immédiate
├── README.md                     # Documentation complète du composant
├── requirements.txt              # Standard library uniquement (dépendances externes nulles)
├── .gitignore                    # Exclusion des caches (__pycache__, .pytest_cache)
├── backend2/                     # Code source
│   ├── __init__.py               # Exporte KnowledgeProvider et KnowledgeRepository
│   ├── models.py                 # Dataclasses immuables (CropProfile, RuleDefinition, Candidate...)
│   ├── repository.py             # Lecture et parsing multi-arbres dans knowledge/
│   ├── provider.py               # Façade publique et adaptateur pour Backend 1
│   └── catalog.py                # Helper d'accès repository()
├── knowledge/                    # Forêt de connaissances agronomiques (Section 14)
│   ├── crops/                    # T1 - Profils de cultures (tomato.json, potato.json, irish_potato.json)
│   ├── rules/                    # T1 - Règles d'ancrage racine de profil (tomato_profile.json...)
│   ├── soils/                    # T2 - Aptitude et amendement du sol
│   ├── regional/                 # T3 - Contexte régional & épidémiologique
│   ├── topography/               # T4 - Topographie & aménagement des pentes
│   ├── climate/                  # T5 - Conditions climatiques & météo (fortes pluies...)
│   ├── timing/                   # T6 - Fenêtres de semis / repiquage (pluie continue...)
│   ├── practices/                # T7 - Pratiques culturales, tuteurage & rotation
│   ├── risks/                    # T7 - Qualification des risques agronomiques
│   └── version.json              # Version et traçabilité des sources agronomiques
└── tests/                        # Tests unitaires
    ├── test_repository.py        # Validation du chargement multi-arbres
    └── test_provider.py          # Validation de la façade KnowledgeProvider
```

---

## 🔌 Note Importante sur l'Intégration avec Backend 1

Le contrat d'échange principal avec Backend 1 est :
```python
provider.get_relevant_rules(crop_id, context, trees)
```

- Backend 2 implémente un adaptateur dynamique dans [`KnowledgeProvider`](file:///home/skyfall/Documents/KA-DIS/projet/agrisense/backend2/backend2/provider.py) qui instancie à la volée les classes de domaine de Backend 1 (`engine.models.domain.Rule`, etc.).
- Tant que le package `engine.models` de Backend 1 n'est pas fourni, l'appel à cette méthode lèvera une `RuntimeError` explicite indiquant les contrats manquants.
- En attendant, **toute la logique de Backend 2 reste 100% testable et fonctionnelle de manière autonome** via la méthode `get_relevant_rule_definitions(...)`.

---

## ➕ Comment Ajouter une Nouvelle Culture ou Règle ?

1. **Ajouter une culture :** Créer un fichier JSON dans `knowledge/crops/<crop_id>.json` avec les champs requis (`crop_id`, `name`, `family`, `objectives`...).
2. **Ajouter une règle :** Créer un fichier JSON dans `knowledge/rules/<crop_id>_<sujet>.json` spécifiant :
   - `rule_id`, `crop_id`, `tree` (parmi `soil`, `region`, `weather`, `timing`, `practices_risks`, etc.)
   - `conditions` : liste d'expressions conditionnelles (`field`, `operator`, `value`)
   - `candidate` : l'action ou conseil à proposer (`name`, `summary`, `actions`, `reasons`).
