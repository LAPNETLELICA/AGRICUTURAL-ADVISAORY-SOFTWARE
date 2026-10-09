# Worktree Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Merge unique contact, vendor, specialist, and action-guidance features from the contact-recommendation worktree into the main backend without restoring retired knowledge code or losing language support.

**Architecture:** Main remains canonical. Worktree-only contact modules are integrated against the current Cameroon provider and current API/service structure. `languages/` is retained as a forwarding compatibility package to `integrations.presentation`, which stays the sole formatter implementation.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic, SQLAlchemy, Alembic, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-10-08-worktree-consolidation-design.md`

## Global Constraints

- Do not restore `knowledge/`, `backend2/`, or `integrations/knowledge.py`.
- Preserve the current `BASE_CONNAISSANCES_AGRICOLES/` runtime integration.
- Preserve `languages` public formatter imports through forwarding exports.
- Merge same-path files by responsibility; do not overwrite main files from the worktree.
- Never copy generated, runtime, coverage, virtual-environment, or Git metadata.

## Review Focus

- Existing `from languages import MobileFormatter` imports remain valid after consolidation.
- Contact lookup exposes only active, verified records, including when filters are omitted.
- Contact recommendations cannot alter agricultural rules or recommendations.
- Action guidance contains only rule-backed recommendation text and no generated agronomy.
- Database migration chains correctly from the active current Alembic revision.

---

### Task 1: Restore language compatibility without duplicate formatter logic

**Files:**
- Create: `languages/__init__.py`, `languages/formatters.py`, `languages/README.md`
- Test: `tests/integrations/test_formatters_and_adapters.py`

**Interfaces:**
- Consumes: `integrations.presentation.{MobileFormatter,SMSFormatter,VoiceFormatter}`.
- Produces: identical exports from `languages` and `languages.formatters`.

- [ ] Add failing tests importing each formatter from both compatibility paths and asserting object identity with `integrations.presentation`.
- [ ] Run the focused formatter test; expected failure: `ModuleNotFoundError: languages`.
- [ ] Add forwarding-only compatibility modules; do not copy formatter class implementations.
- [ ] Run `pytest tests/integrations/test_formatters_and_adapters.py -q`; expected pass.
- [ ] Commit: `refactor: retain language formatter compatibility`.

### Task 2: Integrate contact persistence and public discovery

**Files:**
- Create: `integrations/database/contact_repository.py`, `api/contacts.py`
- Modify: `integrations/database/tables.py`, `integrations/database/__init__.py`, `api/app.py`
- Create: `migrations/versions/e1a3b6d9f2c4_add_agricultural_contacts.py`
- Test: `tests/integration/test_contact_repository.py`, API contact-route tests

**Interfaces:**
- Produces: `AgriculturalContactRepository.find_public(contact_type, category, crop_id, region, location)` and authenticated `/api/v1/contacts/specialists|vendors` routes.

- [ ] Write failing tests for verified/active filtering, relevance ordering, and 503 without database configuration.
- [ ] Run focused tests; expected failure: missing repository/route.
- [ ] Merge the contact table, repository, migration, app-state wiring, and route implementation with current main database/API code.
- [ ] Run focused repository and API tests; expected pass.
- [ ] Commit: `feat: add verified agricultural contact directory`.

### Task 3: Integrate contact and action guidance into mobile recommendations

**Files:**
- Create: `services/contact_recommendation.py`, `services/action_guidance.py`
- Modify: `engine/models/responses.py`, `api/mobile.py`, `api/app.py`
- Test: `tests/unit/test_contact_recommendation.py`, `tests/unit/test_mobile_contact_response.py`

**Interfaces:**
- Consumes: canonical `Recommendation` after `container.engine.advise`.
- Produces: optional `contact_recommendation` and rule-backed `action_guidance` response fields.

- [ ] Write failing tests for no contact requirement, vendor need, specialist need, irrelevant-image escalation, and non-mutation of the engine recommendation.
- [ ] Run unit tests; expected failure: missing guidance services/fields.
- [ ] Merge services and response/API wiring; retain existing current image analysis and presentation adaptation behavior.
- [ ] Run focused unit tests and mobile API tests; expected pass.
- [ ] Commit: `feat: enrich recommendations with actionable support`.

### Task 4: Consolidate documentation and validate the single main tree

**Files:**
- Modify: `README.md`, `docs/REPOSITORY_ORGANIZATION_MAP.md`, `docs/VALIDATION_REPORT.md`
- Copy as historical planning records: worktree Groq/Fish Audio documents into `docs/superpowers/`
- Test: structure, imports, targeted suites, reference scans

**Interfaces:**
- Consumes: Tasks 1-3 public paths.
- Produces: one documented active source tree with clear retired-path policy.

- [ ] Write failing structure/reference assertions that reject retired knowledge provider paths while accepting `languages` compatibility exports.
- [ ] Copy only missing design/plan documentation; label historical records where appropriate.
- [ ] Run `python scripts/check_structure.py`, targeted pytest suites, `ruff check`, import checks, and `rg` scans.
- [ ] Update validation report with actual command output and any environment limitation.
- [ ] Commit: `docs: record worktree consolidation`.
