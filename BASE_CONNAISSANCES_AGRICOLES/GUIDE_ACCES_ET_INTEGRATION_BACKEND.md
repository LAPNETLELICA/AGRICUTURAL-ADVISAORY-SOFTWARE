# Guide d'Accès et d'Intégration — BASE_CONNAISSANCES_AGRICOLES

Ce document spécifie le chemin d'accès et le mode opératoire par lequel le backend unifié d'AgriSense (`AGRICUTURAL-ADVISAORY-SOFTWARE-backend`) consomme et exploite la base de connaissances agricoles du Cameroun.

---

## 1. Chemins d'Accès Recommandés

Le backend unifié (`AGRICUTURAL-ADVISAORY-SOFTWARE-backend`) charge la base via la variable d'environnement `KNOWLEDGE_PATH`.

Deux configurations sont supportées :

### Option A — Colocalisé (Déploiement Standard & Docker) — *Recommandé*
Le dossier `BASE_CONNAISSANCES_AGRICOLES/` est situé directement à la racine du backend :
```bash
# Chemin relatif depuis la racine de AGRICUTURAL-ADVISAORY-SOFTWARE-backend :
KNOWLEDGE_PATH=BASE_CONNAISSANCES_AGRICOLES
```
Dans `docker-compose.yml` et `Dockerfile` :
```dockerfile
COPY BASE_CONNAISSANCES_AGRICOLES ./BASE_CONNAISSANCES_AGRICOLES
ENV KNOWLEDGE_PATH=BASE_CONNAISSANCES_AGRICOLES
```

### Option B — Chemin Absolu (Développement Multi-Dépôts)
Si le backend principal pointe vers le dépôt `backend2` sans duplication physique :
```bash
# Dans le fichier .env de AGRICUTURAL-ADVISAORY-SOFTWARE-backend :
KNOWLEDGE_PATH=/home/skyfall/Documents/KA-DIS/projet/agrisense/backend2/BASE_CONNAISSANCES_AGRICOLES
```

---

## 2. Comment le Backend Consomme la Base de Connaissances

### 1. Accès Bas Niveau via le Lecteur Canonique
Le module [reader.py](reader.py) fournit la classe `CameroonKnowledgeBase` :
```python
from BASE_CONNAISSANCES_AGRICOLES.reader import CameroonKnowledgeBase

# Instanciation automatique
kb = CameroonKnowledgeBase("BASE_CONNAISSANCES_AGRICOLES")

# Accès aux entités
cultures = kb.list_cultures()             # 6 cultures
regions = kb.list_regions()               # 10 régions
sols = kb.list_sols()                     # 6 types de sols
calendrier = kb.get_calendrier_region("REG_OU")
```

### 2. Adaptation Moteur via l'Adaptateur de Pont
Dans `AGRICUTURAL-ADVISAORY-SOFTWARE-backend/integrations/cameroon_knowledge.py` :
```python
from integrations.cameroon_knowledge import CameroonKnowledgeProvider

# L'adaptateur lit la base et projette les règles sur les 7 arbres T1 à T7
provider = CameroonKnowledgeProvider(root="BASE_CONNAISSANCES_AGRICOLES")

# Consultation du profil de culture Pydantic
profile = provider.get_crop_profile("tomato")

# Extraction des règles déclaratives pour l'évaluateur
rules = provider.get_relevant_rules(
    crop_id="tomato",
    context=agricultural_context,
    trees=[TreeId.SOIL, TreeId.WEATHER, TreeId.TIMING, TreeId.PRACTICES_RISKS]
)
```

### 3. Point d'Entrée Applicatif (Bootstrap)
Dans `AGRICUTURAL-ADVISAORY-SOFTWARE-backend/engine/bootstrap.py` :
```python
settings = Settings.from_env()
knowledge_provider = CameroonKnowledgeProvider(settings.knowledge_path)
```

---

## 3. Commandes de Validation et Test dans le Backend

Depuis la racine de `/home/skyfall/Documents/KA-DIS/projet/agrisense/AGRICUTURAL-ADVISAORY-SOFTWARE-backend` :

1. **Validation d'intégrité de la base (72 fichiers) :**
   ```bash
   python3 scripts/validate_cameroon_knowledge.py
   ```
2. **Démonstration interactive de bout en bout :**
   ```bash
   python3 demo.py
   ```
3. **Auto-test du moteur décisionnel :**
   ```bash
   python3 scripts/self_test.py
   ```
