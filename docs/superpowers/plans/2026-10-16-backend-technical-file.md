# Backend Agricultural Technical File Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate a private, nine-section, Unicode-correct PDF technical file from an actual saved recommendation using the existing backend routes.

**Architecture:** Extend the existing fiche assembler to select safe recommendation, trace, profile, weather, and rule-source facts into nine ordered sections without rerunning the engine. Render the stored content with a Unicode-capable, embedded-font PDF service; keep personal files owner-only and serve them through the current authenticated download route.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy, ReportLab, embedded DejaVu font, pytest, Poppler validation tools.

**Spec:** `docs/superpowers/specs/2026-10-16-backend-technical-file-design.md`

## Global Constraints

- Backend only; no Flutter or web frontend exists in this repository.
- Keep every existing technical-fiche route path and the advisory engine unchanged.
- Never invent a diagnosis, confidence score, dose, treatment interval, date, source, contact, or weather measurement.
- French accents and supported Latin characters must survive PDF rendering and extraction.
- Original governed agronomic wording is retained; only labels are localized to English/French. Honor the frontend's explicit language code before the saved profile; accept regional variants (`fr-CM`, `en-US`) by base language. Unsupported locale falls back to English with a visible note and without a failed download.
- A personal fiche is private even if a legacy record has status `PUBLISHED`.
- No raw exception, stack trace, provider diagnostic, key, or internal path appears in a PDF or client error.
- Continue returning JSON fiche content and a PDF attachment using existing authenticated endpoints.

## Review Focus

- A farmer includes HTML/XML metacharacters or very long text: escape markup, wrap content, and preserve a valid multi-page PDF (Task 2).
- A recommendation has only an insufficient-evidence candidate: mark it preliminary and omit unsupported treatment instructions (Task 1).
- A saved legacy fiche is `PUBLISHED` but contains precise farm context: another farmer receives no list entry, read body, or PDF (Task 3).
- A weather provider fails with an internal URL or exception: neither stored content nor PDF nor HTTP error leaks it (Tasks 1 and 3).
- A language setting is `fr-CM`, `en-US`, or unsupported `es`: regional variants select the right labels, French glyphs render, and `es` falls back to English labels with an explicit note (Tasks 1–3).

---

### Task 1: Assemble nine safe sections from saved recommendation evidence

**Files:**
- Modify: `services/technical_fiche.py`
- Test: `tests/unit/test_technical_fiche.py`
- Test: `tests/integrations/test_education_repairs.py`

**Interfaces:**
- Consumes: `Recommendation`, optional `TraceRecord`, optional `ApplicationProfile`, existing `context` and `weather` dictionaries.
- Produces: `TechnicalFicheService.from_recommendation(*, owner_id: str, recommendation: Recommendation, subject: str, language: str, context: dict[str, object] | None = None, weather: dict[str, object] | None = None, trace: TraceRecord | None = None, profile: ApplicationProfile | None = None) -> TechnicalFiche`. Store the nine sections in an ordered `content["sections"]` list of `{ "id": str, "fields": dict }` objects so PostgreSQL JSON key ordering cannot change document order. Section IDs: `cover`, `executive_summary`, `farm_context`, `diagnosis`, `recommendations`, `action_calendar`, `monitoring`, `safety`, `references`. Preserve useful existing top-level JSON keys such as `general_information` and `follow_up` for compatibility.

- [ ] **Step 1: Write failing tests for structure and provenance.** `test_fiche_contains_nine_ordered_sections_from_real_recommendation_and_trace` asserts primary name/actions equal the engine output, locality and weather come from the trace, source titles and validation status come only from matching rule evaluations, and every required section exists. `test_fiche_with_missing_optional_context_does_not_invent_facts` asserts absent area, variety, dates, dose, and confidence are omitted or explicitly not provided.

```python
assert [item["id"] for item in fiche.content["sections"]] == [
    "cover", "executive_summary", "farm_context", "diagnosis", "recommendations",
    "action_calendar", "monitoring", "safety", "references",
]
assert fiche.content["recommendations"]["primary"] == recommendation.primary.name
assert fiche.content["recommendations"]["steps"] == recommendation.actions
assert fiche.content["farm_context"]["locality"] == "Bafoussam"
assert "confidence" not in fiche.content["diagnosis"]
```
- [ ] **Step 2: Run these tests and confirm RED.** Run `.venv/bin/pytest -q tests/unit/test_technical_fiche.py -k 'nine_ordered or missing_optional'`; expected failure is missing sections/provenance, not a fixture error.
- [ ] **Step 3: Implement the minimal section assembler.** Use trace fields only from a per-section allowlist, `Recommendation.action_guidance` only where present, and `RuleEvaluation.candidate.source` only for referenced rules. Derive locale metadata (`fr-CM`→`fr`, `en-US`→`en`, unsupported→English fallback note) without rewriting governed advice. Retain existing service persistence and data model; avoid a migration.
- [ ] **Step 4: Write failing tests for unsafe and incomplete input.** `test_provider_exception_and_private_keys_never_enter_fiche` supplies an internal provider URL/error and private fields; `test_insufficient_evidence_fiche_is_preliminary` asserts unsupported actions are not presented as treatment and no fabricated confidence, urgency, or dates appear; `test_repeated_create_reuses_owner_recommendation_fiche` asserts stable fiche ID for repeat creation.

```python
assert "provider unavailable" not in str(fiche.content).casefold()
assert "api.openweathermap.org" not in str(fiche.content).casefold()
assert fiche.content["cover"]["validation_status"] == "preliminary"
assert first.fiche_id == repeated.fiche_id
```
- [ ] **Step 5: Run new tests RED, then implement allowlist filtering and idempotent lookup.** Use the saved recommendation ID in content metadata; scope lookup to owner and recommendation, and ensure a previous owner's file is never reused.
- [ ] **Step 6: Verify GREEN and commit.** Run `.venv/bin/pytest -q tests/unit/test_technical_fiche.py tests/integrations/test_education_repairs.py`; then commit only this task's files.

### Task 2: Replace flat Latin-1 PDF with readable Unicode pages

**Files:**
- Create: `services/technical_fiche_pdf.py`
- Add: `services/assets/fonts/DejaVuSans.ttf`, `services/assets/fonts/DejaVuSans-Bold.ttf`, and `services/assets/fonts/LICENSE-DejaVu.txt`
- Modify: `api/technical_fiches.py`
- Modify: `pyproject.toml`, `uv.lock`, `requirements.txt`, `Dockerfile` only as needed to package ReportLab and fonts
- Test: `tests/unit/test_technical_fiche_pdf.py`

**Interfaces:**
- Consumes: stored `TechnicalFiche` from Task 1.
- Produces: `render_technical_fiche(fiche: TechnicalFiche) -> bytes`; existing `GET /api/v1/technical-fiches/{fiche_id}/download` returns those bytes as an attachment.

- [ ] **Step 1: Write failing renderer tests.** `test_pdf_has_nine_ordered_sections_and_french_text` checks `%PDF`, `pdfinfo` success, and `pdftotext` output containing `Agricultural Technical File`, `Références`, and source text with accents. `test_long_actions_and_table_flow_without_clipping` supplies long escaped text (including `<unsafe> &`) and many rows; checks multiple pages and last-row extraction. Skip Poppler-only assertions when its executable is unavailable; keep PDF-byte assertions. `test_unsupported_language_uses_visible_english_fallback` checks the fallback note.

```python
assert pdf.startswith(b"%PDF-")
assert pdfinfo.returncode == 0
assert "Références" in extracted_text
assert "pré-germées" in extracted_text
assert "<unsafe> &" in extracted_text
assert "Action 80" in extracted_text
assert "English labels" in fallback_text
```
- [ ] **Step 2: Run tests and confirm RED.** Run `.venv/bin/pytest -q tests/unit/test_technical_fiche_pdf.py`; expected failure is absent renderer/incorrect glyphs.
- [ ] **Step 3: Add ReportLab and embed font assets.** Register fonts from package-relative paths, not a host-only path. Use A4 `BaseDocTemplate`/Platypus `Paragraph`, `LongTable`, repeated header row, `KeepTogether` for section starts, and page header/footer. Escape input text with `xml.sax.saxutils.escape`; do not place private images in the PDF. Package the font license with the assets. Update dependency lock/export and Docker packaging.
- [ ] **Step 4: Route downloads through `render_technical_fiche`.** Remove the Latin-1 replacement path; preserve content type and attachment filename. Generate in memory and reject empty or invalid renderer output with a safe generic 500 response.
- [ ] **Step 5: Verify GREEN and commit.** Run `.venv/bin/pytest -q tests/unit/test_technical_fiche_pdf.py tests/unit/test_technical_fiche.py`; run `.venv/bin/ruff check services/technical_fiche_pdf.py api/technical_fiches.py`; commit task files.

### Task 3: Connect safe context and enforce personal-file privacy

**Files:**
- Modify: `api/technical_fiches.py`, `api/questionnaire.py`, `services/technical_fiche.py`
- Test: `tests/integrations/test_technical_fiche_api.py`
- Modify: `tests/unit/test_questionnaire_fiche_api.py`, `tests/integrations/test_education_repairs.py`

**Interfaces:**
- Consumes: Task 1 assembler and Task 2 renderer.
- Produces: the current create/list/read/download API contract, with owner-only access to personal fiches. Questionnaire completion returns a private `DRAFT` fiche reference without an automatic publish call.

- [ ] **Step 1: Write failing HTTP tests.** `test_create_list_read_and_download_owned_fiche` runs advisory → create → education list → download and checks PDF headers/bytes; `test_other_farmer_cannot_access_published_legacy_personal_fiche` checks list excludes it and read/download return 404; `test_questionnaire_completion_keeps_fiche_private` checks draft status and no publish call.

`test_frontend_language_code_takes_precedence_without_changing_request_shape` sends the existing `language` field as `fr-CM` with an English profile and asserts French document labels; an omitted field uses the profile's language. The explicit/omitted distinction must use Pydantic's `model_fields_set`, since `FicheCreate.language` currently defaults to `en`.

```python
assert created.status_code == 200
assert downloaded.headers["content-type"] == "application/pdf"
assert downloaded.content.startswith(b"%PDF-")
assert other_farmer_read.status_code == 404
assert other_farmer_download.status_code == 404
assert completed.json()["technical_fiche"]["status"] == "DRAFT"
assert explicit_french.json()["content"]["language"]["rendered"] == "fr"
assert omitted_language.json()["content"]["language"]["rendered"] == "en"
```
- [ ] **Step 2: Run tests and confirm RED.** Run `.venv/bin/pytest -q tests/integrations/test_technical_fiche_api.py tests/unit/test_questionnaire_fiche_api.py`.
- [ ] **Step 3: Pass saved trace/profile into fiche creation.** The API must verify recommendation ownership before assembly and pass the actual saved trace, not a new engine run. Remove questionnaire auto-publication. Make `list_visible` owner-only for generated personal files, including legacy `PUBLISHED` rows; leave status administration but do not use status alone as public authorization.
- [ ] **Step 4: Write and run failure tests RED, then handle safely.** `test_missing_recommendation_or_trace_never_renders_misleading_file` expects 404 for an unknown recommendation and 409 for a saved recommendation missing the trace needed to prove ownership; `test_renderer_exception_returns_generic_error_without_diagnostic` replaces only the renderer and asserts no exception text/API URL is returned. Use existing exception handling conventions and avoid logging secrets.
- [ ] **Step 5: Verify GREEN and commit.** Run `.venv/bin/pytest -q tests/integrations/test_technical_fiche_api.py tests/unit/test_questionnaire_fiche_api.py tests/integrations/test_education_repairs.py`; commit task files.

### Task 4: End-to-end verification and frontend handoff documentation

**Files:**
- Modify: `docs/MOBILE_FRONTEND_API_HANDOFF.md`
- Modify: `docs/TESTING.md` if necessary for PDF validation commands
- Test: `tests/integrations/test_technical_fiche_api.py`

**Interfaces:**
- Consumes: unchanged API route paths and Task 3 private-file behavior.
- Produces: a backend-only frontend integration recipe: create from recommendation ID, retain fiche ID, list owned fiches, GET the authenticated PDF, save/share with the client platform later.

- [ ] **Step 1: Add the final integration assertions.** Confirm actual engine primary action appears in extracted PDF, internal provider diagnostic does not, and a repeat create returns the same owner fiche ID. Run the test RED before any needed final correction.
- [ ] **Step 2: Document exact request/response/download handling.** Explain `DRAFT` visibility, bearer authentication, `Content-Disposition`, non-public personal files, locale fallback, and status/error codes. Do not claim a frontend button exists.
- [ ] **Step 3: Run full verification.** Run `.venv/bin/pytest -q -p no:cacheprovider`; `.venv/bin/ruff check .`; `.venv/bin/ruff format --check .`; `.venv/bin/mypy`; `git diff --check`. If Poppler is present, generate a synthetic sample and run `pdfinfo` and `pdftotext` on it; inspect first/last pages. Report any pre-existing failures by name.
- [ ] **Step 4: Commit the handoff and tests.** Commit only changed task files, then report completed behavior, exact test results, manual API steps, and remaining limitations.
