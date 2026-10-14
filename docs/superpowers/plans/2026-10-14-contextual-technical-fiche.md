# Contextual Technical Fiche Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the questionnaire progress without loops and deliver a contextual, structured, weather-aware technical fiche through the Education API and an A4 PDF download.

**Architecture:** Make the questionnaire a small explicit state machine: each stored `expected_field` canonicalises and records exactly one answer before choosing the next unanswered field or producing a request. Build fiche content as typed structured sections from conversation context, recommendation and trace rather than serialising a raw dictionary; a dedicated PDF renderer consumes those sections. Education delegates discovery and read access to the fiche service so its JSON preview and download refer to the same published artefact.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, pytest, existing advisory engine/weather provider, dependency-free PDF output.

**Spec:** `docs/superpowers/specs/2026-10-14-contextual-technical-fiche-design.md`

## Global Constraints

- A recognised answer must return a new `step.key` or `complete: true`; it must never repeat an answered step.
- Return stable option IDs and labels, and accept both IDs and legacy labels from Flutter.
- Preserve the `language` API field but defer localisation; current content remains in its existing language.
- Use weather data when relevant and available; never render a provider error as advice.
- Do not change recommendation selection, ownership checks, sanitisation or published-only public reads.
- Generate only fiche sections relevant to the advisory context; do not invent agronomic doses, safety intervals or other facts.

## Review Focus

- A Flutter client sends `Start farming` instead of `start_farming`: canonicalise the label and move from `intent` to `crop`.
- A client resubmits a stale answer after a completed conversation: return a clear conflict/business error, never reopen or loop the session.
- A crop problem with crop, symptoms and onset already supplied: complete rather than ask `onset` again.
- Weather data containing an unavailable/provider-error marker: omit it from fiche text, while valid weather warnings remain visible.
- A long fiche exceeding one A4 page: produce a valid PDF with correct `page N/M` footers and no truncated structured section.

### Task 1: Explicit questionnaire transitions and stable options

**Files:**
- Modify: `services/questionnaire.py`
- Modify: `engine/models/conversations.py`
- Modify: `api/questionnaire.py`
- Test: `tests/unit/test_questionnaire_conversations.py`
- Test: `tests/integrations/test_questionnaire_api.py`

**Interfaces:**
- Consumes: `AdvisoryConversation.expected_field`, its `context`, and legacy string answers.
- Produces: `QuestionnaireOption(id: str, label: str)`, `QuestionnaireStep.options: list[QuestionnaireOption]`, and `QuestionnaireService.receive_message(conversation_id: str, message: str) -> QuestionnaireResult` with a strictly advancing next step or `ready_request`.

- [ ] **Step 1: Write failing unit tests for canonical intent and an advancing start-farming route**

```python
def test_visible_start_farming_label_advances_to_crop_and_crop_answer_advances() -> None:
    started = service.start_conversation(farmer_id="farmer-1")
    intent = service.receive_message(started.conversation.conversation_id, "Start farming")
    crop = service.receive_message(intent.conversation.conversation_id, "Tomato")
    assert intent.step.key == "crop"
    assert crop.step.key != "crop"
    assert crop.conversation.context["crop_id"] == "tomato"
```

- [ ] **Step 2: Run the unit test to verify it fails**

Run: `pytest tests/unit/test_questionnaire_conversations.py::test_visible_start_farming_label_advances_to_crop_and_crop_answer_advances -v`

Expected: FAIL because the crop step repeats.

- [ ] **Step 3: Add stable options and canonical transition handling**

Define `QuestionnaireOption` and change `QuestionnaireStep.options` to option objects. Add an option-ID/legacy-label resolver and a per-intent transition map in `QuestionnaireService`; store the resolved value under the currently expected field before `_next_step`. Use the stored fields to select only the next missing question. Mark a conversation completed and persist its recommendation metadata after `ready_request` is produced.

- [ ] **Step 4: Add failing tests for option IDs, stale/completed conversations, and crop-problem completion**

```python
def test_crop_problem_completes_after_onset_without_repeating_a_step() -> None:
    # answer intent, crop, symptoms, then onset
    assert result.ready_request is not None
    assert result.step is None

def test_options_expose_id_and_label_but_accept_legacy_label() -> None:
    assert start.step.options[0].id == "start_farming"
    assert start.step.options[0].label == "Start farming"
```

- [ ] **Step 5: Implement completion/stale-state handling and update the FastAPI payload/result serialisation**

Add `language` to the start/answer request model and conversation context without localisation. Have `/answer` reject completed/stale state with a concrete HTTP business error and return a new `step.key` whenever not complete. Preserve legacy payload compatibility by accepting `answer` as the existing string field.

- [ ] **Step 6: Run focused questionnaire tests**

Run: `pytest tests/unit/test_questionnaire.py tests/unit/test_questionnaire_conversations.py tests/unit/test_questionnaire_completion.py tests/integrations/test_questionnaire_api.py -v`

Expected: PASS.

- [ ] **Step 7: Commit the advancing questionnaire implementation**

```bash
git add services/questionnaire.py engine/models/conversations.py api/questionnaire.py tests/unit/test_questionnaire_conversations.py tests/integrations/test_questionnaire_api.py
git commit -m "fix: advance questionnaire answers without loops"
```

### Task 2: Contextual structured fiche assembly

**Files:**
- Modify: `services/technical_fiche.py`
- Modify: `api/technical_fiches.py`
- Test: `tests/unit/test_technical_fiche.py`
- Test: `tests/integrations/test_technical_fiches_api.py`

**Interfaces:**
- Consumes: `Recommendation`, its `TraceRecord`, completed conversation context, `subject`, and `language`.
- Produces: `TechnicalFiche.content` with `general_information`, `diagnosis`, `recommendations`, `action_calendar`, `safety`, and `follow_up` sections; absent irrelevant sections are omitted.

- [ ] **Step 1: Write failing fiche-service tests for section selection and private-data sanitisation**

```python
def test_problem_fiche_contains_diagnosis_protection_calendar_and_safety() -> None:
    fiche = service.from_recommendation(..., context={"intent": "crop_problem", "symptoms": "yellow spots"}, trace=trace)
    assert "diagnosis" in fiche.content
    assert "crop_protection" in fiche.content["recommendations"]
    assert "action_calendar" in fiche.content
    assert "farmer_id" not in str(fiche.content)
```

- [ ] **Step 2: Run the fiche-service test to verify it fails**

Run: `pytest tests/unit/test_technical_fiche.py::test_problem_fiche_contains_diagnosis_protection_calendar_and_safety -v`

Expected: FAIL because fiche content is presently a flat dictionary.

- [ ] **Step 3: Implement structured context-aware fiche generation**

Add a focused internal builder in `TechnicalFicheService` that selects planting/soil, nutrition, protection/biocontrol, irrigation and safety subsections based on intent, collected facts and recommendation actions/warnings. Build calendar rows from validated actions with neutral `À planifier` status; render unknown follow-up facts as `À confirmer` only where useful. Extend `from_recommendation` to receive optional context/trace without breaking existing callers.

- [ ] **Step 4: Write failing API tests for contextual creation, ownership and no provider-error leakage**

```python
def test_created_fiche_omits_weather_provider_failure_and_keeps_valid_weather_warning(client) -> None:
    created = client.post("/api/v1/technical-fiches", json=payload, headers=headers)
    assert "provider unavailable" not in str(created.json()).lower()
    assert "heavy rain" in str(created.json()).lower()
```

- [ ] **Step 5: Wire recommendation trace and conversation context into fiche creation**

Resolve the recommendation trace and completed conversation context in the endpoint, pass only authorised/sanitised values to the builder, and map missing recommendation/trace/context into existing HTTP error conventions.

- [ ] **Step 6: Run focused fiche tests**

Run: `pytest tests/unit/test_technical_fiche.py tests/integrations/test_technical_fiches_api.py -v`

Expected: PASS.

- [ ] **Step 7: Commit structured fiche generation**

```bash
git add services/technical_fiche.py api/technical_fiches.py tests/unit/test_technical_fiche.py tests/integrations/test_technical_fiches_api.py
git commit -m "feat: build contextual structured technical fiches"
```

### Task 3: Paginated A4 PDF rendering

**Files:**
- Modify: `api/technical_fiches.py`
- Test: `tests/integrations/test_technical_fiches_api.py`

**Interfaces:**
- Consumes: structured `TechnicalFiche.content`.
- Produces: `_pdf_document(fiche: TechnicalFiche) -> bytes` containing correctly wrapped A4 pages and `page N/M` footers.

- [ ] **Step 1: Write a failing download test for PDF format, section text and page footer**

```python
def test_downloaded_fiche_is_a_paginated_a4_pdf(client) -> None:
    response = client.get(f"/api/v1/technical-fiches/{fiche_id}/download", headers=headers)
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content.startswith(b"%PDF-")
    assert b"page 1/" in response.content
```

- [ ] **Step 2: Run the download test to verify it fails**

Run: `pytest tests/integrations/test_technical_fiches_api.py::test_downloaded_fiche_is_a_paginated_a4_pdf -v`

Expected: FAIL because the current single-page renderer has no pagination or structured layout.

- [ ] **Step 3: Replace the flat PDF serializer with a structured A4 renderer**

Implement a small dependency-free layout helper that wraps text, emits section headings and calendar rows, calculates pages before writing the footer, and uses a safe PDF string encoder. Render only present fiche sections; use a deterministic filename based on fiche crop/ID.

- [ ] **Step 4: Run fiche API tests**

Run: `pytest tests/integrations/test_technical_fiches_api.py -v`

Expected: PASS.

- [ ] **Step 5: Commit the PDF renderer**

```bash
git add api/technical_fiches.py tests/integrations/test_technical_fiches_api.py
git commit -m "feat: render paginated technical fiche PDFs"
```

### Task 4: Education fiche discovery and end-to-end verification

**Files:**
- Modify: `api/education.py`
- Modify: `api/app.py`
- Test: `tests/integrations/test_v1_extensions.py`
- Test: `tests/integrations/test_questionnaire_fiche_journey.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: `TechnicalFicheService.list_published(crop_id, subject)` and `TechnicalFicheService.get(fiche_id)`.
- Produces: `GET /api/v1/education/technical-fiches` and `GET /api/v1/education/technical-fiches/{fiche_id}` responses with `download_url`, plus a documented questionnaire-to-fiche journey.

- [ ] **Step 1: Write failing Education API tests for published fiche list, detail and download URL**

```python
def test_education_exposes_published_fiche_with_download_url(client) -> None:
    listed = client.get("/api/v1/education/technical-fiches", headers=headers)
    assert listed.json()[0]["download_url"].endswith("/download")
```

- [ ] **Step 2: Run the Education test to verify it fails**

Run: `pytest tests/integrations/test_v1_extensions.py::test_education_exposes_published_fiche_with_download_url -v`

Expected: FAIL with 404 because Education has no fiche endpoints.

- [ ] **Step 3: Add published-only Education fiche endpoints**

Delegate to `technical_fiche_service`, preserve existing authentication conventions, filter by crop/subject, return only published fiches, and construct a relative download URL. Do not duplicate fiche storage or publication logic.

- [ ] **Step 4: Write a failing end-to-end test for the no-loop journey**

```python
def test_questionnaire_answers_complete_then_publish_view_and_download_fiche(client) -> None:
    keys = [answer_step(client, conversation_id, answer)["step"]["key"] for answer in answers[:-1]]
    assert len(keys) == len(set(keys))
    assert final["complete"] is True
    assert client.get(download_url, headers=headers).status_code == 200
```

- [ ] **Step 5: Implement only endpoint wiring/documentation needed by the end-to-end test**

Document option IDs and legacy-label compatibility, the non-loop completion guarantee, fiche publication/education flow, weather treatment and the explicitly deferred localisation scope in `README.md`.

- [ ] **Step 6: Run focused integration tests and then the full suite**

Run: `pytest tests/integrations/test_questionnaire_api.py tests/integrations/test_technical_fiches_api.py tests/integrations/test_questionnaire_fiche_journey.py tests/integrations/test_v1_extensions.py -v && pytest -q`

Expected: PASS. Record any unrelated pre-existing failures before handoff.

- [ ] **Step 7: Commit Education integration and documentation**

```bash
git add api/education.py api/app.py README.md tests/integrations/test_v1_extensions.py tests/integrations/test_questionnaire_fiche_journey.py
git commit -m "feat: expose technical fiches in education"
```
