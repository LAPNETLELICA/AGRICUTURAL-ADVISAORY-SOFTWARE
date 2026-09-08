# Merge Guide: Developer 2 Knowledge into Developer 1 Engine

This procedure preserves the conception book's WHAT/HOW separation while merging
Developer 2's validated crop forest into this repository.

Replace the example branch name `developer-2-knowledge` with the actual remote branch.

## 1. Expected ownership

| Path | Primary owner | Merge rule |
| --- | --- | --- |
| `engine/**` | Developer 1 | Developer 2 must not add crop-specific branches |
| `knowledge/**` | Developer 2 | Developer 1 reviews contract/operability, not agronomic truth |
| `tests/rules/**` | Developer 2 + shared review | Must accompany validated rules |
| `tests/scenarios/**` | Shared | Both developers approve expected outcomes |
| `engine/models/**`, `engine/interfaces/**` | Shared | Contract changes agreed before content merge |
| `knowledge/rules/schemas/**` | Shared | Schema changes require both developers' approval |
| `integrations/**`, `api/**`, `languages/**`, `engine/bootstrap.py` | Shared | Provider/API changes require integration tests |

Developer 2's branch should normally change only the documented domain folders and
its rule/scenario tests. It must preserve this Section 14 alignment:

```text
knowledge/
├── crops/          # T1
├── soils/          # T2
├── regional/       # T3
├── topography/     # T4
├── climate/        # T5
├── timing/         # T6
├── practices/      # T7
├── risks/          # T7
├── rules/
└── version.json
```

The included `draft` Irish-potato files are collaboration fixtures. Developer 2 may
replace those files with reviewed equivalents using the same stable IDs, or add new
files with new stable IDs; do not create a second `knowledge/production/` tree.

## 2. Pre-merge checks on Developer 2's branch

Developer 2 runs:

```bash
git checkout developer-2-knowledge
git pull --ff-only
uv sync --extra dev
uv run python scripts/validate_knowledge.py knowledge \
  --allow-status draft --allow-status validated
uv run pytest tests/rules tests/scenarios
git status --short
```

The final command must show no unintended generated files, secrets, credentials,
farmer data, or local environments.

Every `validated` item must include `source.validated_by`. Every hard constraint must
be validated. Crop IDs referenced by rules must exist as profiles.

## 3. Inspect the incoming change before merging

On the integration branch:

```bash
git fetch origin
git checkout developer-1-integration
git pull --ff-only
git status --short
git diff --name-status HEAD..origin/developer-2-knowledge
git diff HEAD..origin/developer-2-knowledge -- knowledge tests/rules tests/scenarios
```

Stop and ask Developer 2 to revise if the diff contains:

- agricultural thresholds inside `engine/`, `api/`, or Flutter logic;
- rules without crop/source/version/status;
- real secrets or real farmer identifiers;
- deletion of shared tests/schemas without an agreed contract change;
- validated status without an agronomy reviewer;
- an ML model used as the V1 decision authority.

## 4. Perform the merge

```bash
git merge --no-ff origin/developer-2-knowledge
```

If there is a conflict, inspect it:

```bash
git status
git diff --name-only --diff-filter=U
```

Resolve according to this policy:

| Conflict | Resolution |
| --- | --- |
| Different crop/rule JSON files | Preserve Developer 2 content after schema validation |
| `version.json` | Create one monotonic merged version and retain source metadata |
| JSON schema / Pydantic model | Do not choose one side silently; agree and test a shared contract |
| Rule test expected output | Agronomic expectation requires Developer 2/expert approval; engine mechanics require Developer 1 approval |
| Engine code containing crop-specific logic | Keep generic engine; move the threshold/action into a rule |
| Draft and validated items | Preserve status/source metadata; reject duplicate stable IDs |

After editing resolved files:

```bash
git add <resolved-files>
git commit
```

To abandon an unresolved merge safely:

```bash
git merge --abort
```

## 5. Validate the merged knowledge

First validate all authored statuses so malformed drafts are caught:

```bash
uv run python scripts/validate_knowledge.py knowledge \
  --allow-status draft --allow-status validated
```

Then validate the exact production view:

```bash
APP_ENV=production uv run python scripts/validate_knowledge.py \
  knowledge --allow-status validated
```

Verify metadata manually:

```bash
APP_ENV=production KNOWLEDGE_PATH=knowledge \
  uv run uvicorn api.app:app --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
curl -sS http://127.0.0.1:8000/api/v1/knowledge/version
curl -sS http://127.0.0.1:8000/api/v1/crops
```

Confirm:

- `production_ready` is true in Developer 2's metadata;
- crop count and rule count match the reviewed catalogue;
- only validated statuses appear;
- every expected pilot crop is listed.

## 6. Run all gates

```bash
python scripts/check_structure.py
uv run pytest
uv run pytest --cov=api --cov=engine --cov=integrations --cov=languages --cov-report=term-missing
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

Run the live API smoke test while the production-configured server is active:

```bash
uv run python scripts/smoke_test.py
```

The supplied smoke script expects `irish-potato`. If Developer 2 uses a different
canonical crop ID, update the smoke fixture and document the mapping in the same
merge commit.

## 7. Scenario acceptance

For every pilot crop, confirm at least one complete scenario with:

- explicit `crop_id`;
- region/locality;
- Past, Present, and Future evidence;
- T1 plus all contextually relevant trees;
- positive, negative, and boundary rule behavior;
- any hard exclusion;
- score breakdown and stable ranking;
- conflict winner and rejected alternatives where applicable;
- recommendation reasons, warnings, actions, and rule references;
- complete stored trace;
- Mobile and SMS channel differences.

Do not approve solely because the API returns HTTP 200. The agronomic outcome and
source trace must be reviewed.

## 8. Connect runtime configuration

Development preview of the merged knowledge (includes statuses permitted by the
environment):

```bash
export KNOWLEDGE_PATH=knowledge
uv run uvicorn api.app:app --reload
```

Production:

```bash
export APP_ENV=production
export KNOWLEDGE_PATH=knowledge
uv run uvicorn api.app:app --host 0.0.0.0 --port 8000
```

Update Docker/secret-manager environment settings in deployment; never hard-code the
path or credentials into engine modules.

## 9. Post-merge Git steps

```bash
git status --short
git log --oneline --decorate -5
git push origin developer-1-integration
```

Open the integration pull request with:

- knowledge version and crop/rule counts;
- agronomy validator(s);
- sources added/changed;
- test and coverage results;
- conflict-resolution decisions;
- known limitations;
- rollback commit/previous knowledge version.

After the merge reaches the main branch, tag a reproducible baseline according to the
team's release policy, for example:

```bash
git tag -a v1.0.0-knowledge.1 -m "V1 engine plus validated crop knowledge baseline"
git push origin v1.0.0-knowledge.1
```

## 10. Rollback after a completed merge

Do not rewrite shared history. Identify the merge commit, then revert it:

```bash
git log --merges --oneline -10
git revert -m 1 <merge-commit-sha>
git push origin developer-1-integration
```

If only a knowledge release must roll back in deployment, point
`KNOWLEDGE_PATH`/the deployed artifact at the last reviewed version and record that
operational change. Never silently downgrade sources or statuses inside the active
files.

## Final merge checklist

- [ ] Incoming paths respect ownership.
- [ ] No secret, farmer PII, or local artifact is committed.
- [ ] All production crops and rules validate.
- [ ] Validated items identify an agronomy validator.
- [ ] Hard constraints are sourced and tested.
- [ ] Rule positive/negative/boundary tests pass.
- [ ] Shared scenarios pass for Mobile and SMS.
- [ ] Trace includes Past/Present/Future, rules, constraints, scores, conflicts.
- [ ] Formatting/lint/type gates pass.
- [ ] Production environment loads validated content only.
- [ ] API smoke test passes.
- [ ] Knowledge version/counts and rollback version are recorded.
