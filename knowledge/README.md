# Developer 2 Knowledge Contract

Developer 2 owns the agricultural **WHAT TO ADVISE** content in this directory.
Developer 1 owns the generic reasoning engine and must not rewrite crop knowledge as
Python `if/else` logic.

## Section 14 layout

This directory follows the conception book exactly:

```text
knowledge/
├── __init__.py            # Python package entry point (exports KnowledgeProvider, KnowledgeRepository)
├── catalog.py             # Development catalog convenience accessor
├── models.py              # Knowledge dataclasses & Section 14 domain-to-tree mappers
├── provider.py            # KnowledgeProvider implementation
├── repository.py          # KnowledgeRepository file reader & query engine
├── version.json           # Catalog version & multi-crop bibliographic traceability
├── crops/                 # T1 — Crop Profile root (tomato.json, irish_potato.json)
├── soils/                 # T2 — Soil suitability & improvement rules
├── regional/              # T3 — Regional & altitude agro-climatic context
├── topography/            # T4 — Terrain, slope & anti-erosion rules
├── climate/               # T5 — Weather, heavy rainfall & disease alerts
├── timing/                # T6 — Planting, nursery & transplanting windows
├── practices/             # T7 — Agricultural practices, ridging, trellising & rotation
├── risks/                 # T7 — Crop risks and pathology monitoring
└── rules/
    └── schemas/           # Shared JSON reference schemas (crop-profile, rule)
```

`crops/*.json` contains one Crop Profile object per file. JSON files in `rules/`,
`soils/`, `regional/`, `topography/`, `climate/`, `timing/`, `practices/`, and
`risks/` contain `{ "rules": [...] }` conforming to `rules/schemas/rule.schema.json`.

The knowledge base currently hosts **two fully documented crops** across all 7 Section 14 trees:
1. **Tomate (`tomato`)** — Sourced from Guide technique IFATI (MINEFOP Cameroun) & SDRdag 2016.
2. **Pomme de terre (`irish-potato`)** — Sourced from Guide pratique de la culture de la pomme de terre en Afrique de l'Ouest (CDE / MINADER Cameroun, Félix Teouaba) & Manuel FiBL Afrique.

## Required governance fields

Every crop and rule must contain:

- stable `crop_id`;
- `version`;
- `status` (`draft`, `validated`, `deprecated`, or `test_only`);
- `source.title` and, when available, `source.uri` and `source.section`;
- `source.validated_by` for `validated` content;
- `source.validated_at` when validation time is known.

Every rule also needs a stable `rule_id`, one `domain` (`T1`-`T7`), a priority,
and a candidate. A matched rule may use `requires_trees` to deepen traversal.

## Domain-to-folder rule

| Folder | Expected tree | Content |
| --- | --- | --- |
| `crops/` | T1 data | Crop profiles, one object per file |
| `rules/` | Usually T1 | Root/profile and shared declarative rules |
| `soils/` | T2 | Soil suitability and improvement |
| `regional/` | T3 | Regional and geographic context |
| `topography/` | T4 | Terrain and land suitability |
| `climate/` | T5 | Weather and climate fit |
| `timing/` | T6 | Planting and cultivation timing |
| `practices/` | T7 | Practices and crop rotation |
| `risks/` | T7 | Crop-specific risks |

The runtime enforces the folder/domain mapping for T2-T7. `rules/` accepts generic
or T1 root rules. A misplaced rule therefore fails validation before startup.

## Validation

During authoring:

```bash
uv run python scripts/validate_knowledge.py knowledge \
  --allow-status draft --allow-status validated
```

Production gate:

```bash
APP_ENV=production uv run python scripts/validate_knowledge.py \
  knowledge --allow-status validated
uv run pytest tests/rules tests/scenarios
```

For each validated rule, Developer 2 adds a positive, negative, lower-boundary,
upper-boundary, missing-evidence, source/version, and relevant conflict or hard-
constraint test. Never mark a hard constraint `validated` without agronomy review.
Scores rank candidates; they are not probabilities and cannot override hard safety
constraints.
