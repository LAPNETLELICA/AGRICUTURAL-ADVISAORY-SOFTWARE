# Developer 2 Knowledge Contract

Developer 2 owns the agricultural **WHAT TO ADVISE** content in this directory.
Developer 1 owns the generic reasoning engine and must not rewrite crop knowledge as
Python `if/else` logic.

## Section 14 layout

This directory follows the conception book exactly:

```text
knowledge/
├── version.json
├── crops/                 # T1 — Crop Profile root
├── soils/                 # T2 — suitability and improvement
├── regional/              # T3 — regional/geographic context
├── topography/            # T4 — terrain and land suitability
├── climate/               # T5 — weather and climate fit
├── timing/                # T6 — planting/cultivation timing
├── practices/             # T7 — practices and rotation
├── risks/                 # T7 — crop risks
└── rules/
    └── schemas/           # Shared JSON reference schemas
```

`crops/*.json` contains one Crop Profile object per file. JSON in `rules/`,
`soils/`, `regional/`, `topography/`, `climate/`, `timing/`, `practices/`, and
`risks/` contains either a list of rules or `{ "rules": [...] }`. Filenames are
organizational; stable IDs inside files are authoritative.

The included Irish-potato files are safe-to-run collaboration fixtures only. They
are `draft`, explicitly unvalidated, and excluded when `APP_ENV=production`.

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
