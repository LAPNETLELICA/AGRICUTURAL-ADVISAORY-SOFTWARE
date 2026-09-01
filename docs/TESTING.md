# Testing and Acceptance Guide

The test design follows Section 17 of the conception book. Tests separate engine
mechanics from agricultural truth so each developer can review the correct layer.

## Install test tools

```bash
uv sync --extra dev
```

Or:

```bash
python -m pip install -r requirements-dev.txt
python -m pip install --no-deps -e .
```

## Test layers

| Layer | Directory | What it proves |
| --- | --- | --- |
| Unit | `tests/engine/` | Evaluator, selector, constraints, scoring, ranker, conflicts, builder |
| Rule | `tests/rules/` | Positive, negative, missing, and boundary behavior for knowledge rules |
| Integration | `tests/integrations/` | Knowledge loader, context/weather fallback, SMS, API |
| Scenario | `tests/scenarios/` | Complete crop-first multi-tree decisions |
| Channel | scenario/API tests | Mobile interactive vs proactive SMS scoring/presentation |
| Trace | scenario/API tests | Full evidence and final recommendation linkage |
| Regression | rules/scenarios | Stable validated outcome after knowledge change |

## Commands

Complete suite:

```bash
uv run pytest
```

One layer:

```bash
uv run pytest tests/engine
uv run pytest tests/rules
uv run pytest tests/integrations
uv run pytest tests/scenarios -m scenario
```

One failing test with details:

```bash
uv run pytest tests/scenarios/test_bafoussam_potato.py -vv -x
```

Coverage:

```bash
uv run pytest --cov=api --cov=engine --cov=integrations --cov=languages \
  --cov-report=term-missing --cov-report=html --cov-branch
```

The configured gate is 85%. Open `htmlcov/index.html` for detail.

Quality checks:

```bash
python scripts/check_structure.py
uv run ruff check .
uv run ruff format --check .
uv run mypy
python -m compileall -q api engine integrations languages scripts tests
```

Offline core check (not a replacement for pytest/API tests):

```bash
PYTHONPATH=. python scripts/self_test.py
```

## Conception-book scenario

The included scenario uses:

```text
crop: Irish potato
location: Bafoussam, West Region
month: August
weather: heavy rainfall and 3 consecutive rain days
land: flatland
soil evidence: poor drainage (to exercise T2 improvement)
```

Expected mechanics:

- T1 is selected first;
- evidence adds T2, T3, T4, T5, and T6;
- the matched T5 draft rule expands T7;
- rules are evaluated before constraints/scoring;
- Mobile ranks disease watch, drainage improvement, timing, then profile context;
- SMS uses SMSPriority and produces a different numeric score;
- recommendation includes risk, soil action, timing, reasons, warnings, actions;
- trace links to the same recommendation and contains all seven trees.

These expectations test the conception flow. They do **not** certify the draft demo
content as correct agronomy.

## Live API validation

Start the API:

```bash
uv run uvicorn api.app:app --host 127.0.0.1 --port 8000
```

Run:

```bash
uv run python scripts/smoke_test.py
```

Check OpenAPI manually at <http://127.0.0.1:8000/docs>. Confirm request validation
returns 422 for missing/invalid fields, unknown crop returns 404, and a created
recommendation can be retrieved with its trace.

## Developer 2 rule acceptance template

For a rule `crop.domain.rule.001`, add tests like:

```python
def test_rule_matches_valid_evidence(...): ...
def test_rule_rejects_opposite_evidence(...): ...
def test_rule_lower_boundary(...): ...
def test_rule_upper_boundary(...): ...
def test_rule_missing_evidence_is_insufficient(...): ...
def test_rule_source_and_version(...): ...
```

If the rule has a hard constraint:

```python
def test_hard_constraint_excludes_candidate(...): ...
def test_score_cannot_restore_excluded_candidate(...): ...
```

If rules conflict:

```python
def test_conflict_records_winner_loser_priority_and_evidence(...): ...
```

## Production acceptance criteria

- All automated gates pass on Python 3.11 and 3.12.
- Knowledge validates with `--allow-status validated` only.
- Every pilot crop has rule and scenario coverage.
- External-provider timeout/failure produces explicit uncertainty.
- No test relies on real network, real farmer data, or real SMS delivery.
- Repeated runs produce stable ranking for identical input.
- Hard constraints always eliminate affected candidates.
- Insufficient evidence never produces a fabricated threshold/value.
- Trace/recommendation IDs link both directions through repository retrieval.
- SMS content stays within configured length.
- Production deployment tests authentication/RBAC once that open decision is closed.

## Test data rules

- Use synthetic farmer IDs and virtual recipient IDs.
- Keep knowledge fixtures clearly `test_only` or `draft`.
- Never place secrets, phone numbers, images, or real farmer context in the repository.
- Freeze validated regression outcomes only after Developer 2/agronomy approval.
