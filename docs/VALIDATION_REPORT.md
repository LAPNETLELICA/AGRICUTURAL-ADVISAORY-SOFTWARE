# Build Validation Report

Date: 2026-09-01 (UTC)

## Source analysis

- Read all 24 pages of the v3.0 conception book.
- Visually inspected the architecture, Developer 1 component, deployment, and
  repository/work-split diagrams.
- Copied the source PDF byte-for-byte into `docs/reference/`.
- Source/reference SHA-256:
  `5fd3de6b354ff3272ee37c67f9562ab0e5a8b9a100032d90cbdbad1e708383cd`.

## Checks executed successfully

- Section 14 structure check for all required top-level ownership paths; the legacy
  `src/agricultural_advisory/` and `knowledge/demo/` paths are absent.
- Python compilation for `api/`, `engine/`, `integrations/`, `languages/`,
  `scripts/`, and `tests/`.
- JSON parsing for all 9 knowledge/schema files and TOML parsing for project metadata.
- Syntax/import-target checks for all 69 Python files and local Markdown-link checks.
- Pydantic validation of the draft Crop Profile and all five domain-split rules.
- Folder/domain enforcement for T2-T7 knowledge files.
- `scripts/validate_knowledge.py` with draft + validated status view.
- `scripts/validate_knowledge.py` with the production-only validated view.
- `scripts/demo_request.py` JSON serialization.
- ZIP CRC/integrity check plus required/forbidden path inspection.
- `scripts/self_test.py`, covering:
  - complete Bafoussam/Irish-potato crop-first scenario;
  - T1-T7 selection/expansion;
  - MobileScore vs SMSPriority separation;
  - condition evaluation;
  - soft constraints;
  - deterministic ranking and conflict resolution;
  - recommendation and full trace persistence;
  - Crop Passport creation/update;
  - SMS formatting and virtual-inbox delivery;
  - production exclusion of draft knowledge.

Result: `OFFLINE CORE SELF-TEST PASSED`.

## Test suite delivered

Fifty-two pytest test functions are included across unit, rule, integration, scenario,
channel, trace, configuration, storage, and API layers. Parameterization expands this
to additional individual cases. One test permanently guards the Section 14 layout.

## Environment limitation

The build workspace contained Pydantic 2.13.4 but not FastAPI, Uvicorn, HTTPX,
pytest, Ruff, or mypy. Its configured Python package registry returned HTTP 403, so
those external packages could not be downloaded here. Consequently, the FastAPI
TestClient suite, coverage, Ruff, and mypy commands could not be executed in this
workspace.

This is an environment/network limitation rather than a skipped project dependency.
All dependencies are declared and pinned/ranged in `pyproject.toml`,
`requirements.txt`, and `requirements-dev.txt`. Run the normal gates after `uv sync
--extra dev` on a developer machine or approved package mirror:

```bash
uv run pytest
python scripts/check_structure.py
uv run pytest --cov=api --cov=engine --cov=integrations --cov=languages \
  --cov-report=term-missing
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

The runtime pins were cross-checked against official project releases current on the
report date: FastAPI 0.141.1, Pydantic 2.13.4, and Uvicorn 0.52.4.
