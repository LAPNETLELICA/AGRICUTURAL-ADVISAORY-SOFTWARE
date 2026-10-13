# Adaptive Farmer Questionnaire Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement task-by-task.

**Goal:** Add a backend API that guides farmers through adaptive, profile-aware questions and produces an existing mobile advisory request.

**Architecture:** A dedicated questionnaire service keeps a session's collected answers, obtains known locality facts from validated knowledge, and returns one next question at a time. It never changes advisory rules; completion maps its context to `MobileAdvisoryRequest` and reuses existing voice and media endpoints.

**Completion rule:** When collected context is sufficient for the selected intent, the API stops asking questions, creates the existing mobile advisory request, calls the unchanged engine, and returns its recommendation.

**Tech Stack:** Python, FastAPI, Pydantic, existing knowledge provider, passport/profile services, pytest.

**Spec:** `docs/superpowers/specs/2026-10-12-adaptive-farmer-questionnaire-design.md`

## Global Constraints

- Never alter recommendation selection or invent agricultural facts.
- Query validated locality/region knowledge before asking any related question.
- Accept free text at every question, plus existing voice transcription and protected image references.
- Use crop-passport facts first; ask prior crop/manure only when they are unavailable.
- Keep beginner prompts simple and always offer “I do not know”.

### Task 1: Questionnaire domain and locality fact lookup

**Files:** Create `services/questionnaire.py`, `tests/unit/test_questionnaire.py`; modify `integrations/cameroon_knowledge.py`.

- [ ] Write failing tests for known-locality facts suppressing terrain prompts, unknown locality producing a terrain prompt, and free-text answers changing the next step.
- [ ] Implement `QuestionnaireService.start()` and `QuestionnaireService.answer()` with `QuestionnaireStep` responses, an explicit `free_text` field, profile-aware copy, and validated knowledge lookup.
- [ ] Run `pytest tests/unit/test_questionnaire.py -v` and commit with the final combined user-authorized commit.

### Task 2: Passport-aware context and completion

**Files:** Modify `services/questionnaire.py`, `engine/models/requests.py`; create `tests/unit/test_questionnaire_completion.py`.

- [ ] Write failing tests proving passport context suppresses repeated crop/manure questions and no-passport start-farming asks previous crop and usual manure.
- [ ] Implement completion into a valid `MobileAdvisoryRequest`, preserving typed question, evidence, location, and “unknown” answers.
- [ ] Run the questionnaire unit tests and existing mobile request tests.

### Task 3: Questionnaire API and media integration

**Files:** Create `api/questionnaire.py`, modify `api/app.py`, create `tests/integrations/test_questionnaire_api.py`.

- [ ] Write failing authenticated API tests for start, answer, free-text, transcription handoff, and image-reference handoff.
- [ ] Add admin-independent farmer endpoints, ownership checks, and clear recovery responses for unavailable transcription/image analysis.
- [ ] Run `pytest tests/integrations/test_questionnaire_api.py tests/integrations/test_api.py -v`.

### Task 4: Verification and documentation

**Files:** Modify `README.md`, `docs/TESTING.md`; tests from Tasks 1–3.

- [ ] Document the adaptive behavior, data boundaries, and existing voice/picture prerequisites.
- [ ] Run the focused suite, database migration verification, and the full suite with PostgreSQL available; record any pre-existing failures.
