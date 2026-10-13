# Persistent Advisory Conversations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist multiple farmer-owned advisory conversations and make questionnaire text contextual, adaptive, and able to return a recommendation automatically.

**Architecture:** Add conversation/message models and repositories with in-memory and PostgreSQL adapters. Make `QuestionnaireService` own text interpretation, context collection, next-question selection, and readiness. Keep the three questionnaire URLs, add optional `conversation_id`, and add one history endpoint. Extract direct mobile-advisory processing into a shared service so direct and questionnaire recommendations behave identically.

**Tech Stack:** Python 3.11, FastAPI, Pydantic 2, SQLAlchemy 2, Alembic, PostgreSQL JSONB, pytest.

**Spec:** `docs/superpowers/specs/2026-10-13-persistent-advisory-conversations-design.md`

## Global Constraints

- Preserve questionnaire `start`, `answer`, and `complete` URLs and required fields.
- Add only optional `conversation_id` fields to existing request/response bodies.
- Add `GET /api/v1/questionnaire/conversations/{conversation_id}` with ownership enforcement.
- Persist every farmer and assistant message in sequence within its conversation.
- Call the existing engine only after intent-specific required context is available.
- Reuse direct mobile media validation, image analysis, guidance, contacts, and presentation for automatic results.

## Review Focus

- `Start farming` must route like its internal option ID.
- A new issue during a pending prompt preserves history but resets only incomplete intent-specific facts.
- Two open conversations for one farmer never exchange messages, context, or recommendations.
- Another farmer's conversation ID returns `403` without disclosure.
- A legacy request without `conversation_id` uses only the latest open conversation or returns a clear `400`.

---

### Task 1: Conversation models and repositories

**Files:**
- Create: `engine/models/conversations.py`, `integrations/database/conversation_repository.py`, `migrations/versions/<revision>_add_advisory_conversations.py`
- Modify: `engine/interfaces/providers.py`, `engine/models/repositories.py`, `engine/bootstrap.py`, `integrations/database/tables.py`, `integrations/database/__init__.py`
- Test: `tests/unit/test_conversation_repository.py`, `tests/integration/test_conversation_repository.py`

**Interfaces:** Define `AdvisoryConversation`, `ConversationMessage`, `ConversationStatus`, and `ConversationRepository`. The repository exposes `create`, `get`, `latest_open`, `save`, and `list_messages`.

- [ ] **Step 1: Write failing repository tests**

Test that two conversations for one farmer keep interleaved messages separate and ordered, and that `latest_open` excludes completed conversations.

- [ ] **Step 2: Verify RED**

Run: `pytest tests/unit/test_conversation_repository.py -v`

Expected: FAIL because models and repository are absent.

- [ ] **Step 3: Implement in-memory models and repository**

Use UUID IDs, `open|completed` status, intent, expected field, JSON-compatible context, timestamps, and monotonically sequenced `farmer|assistant` messages. Return deep copies so callers cannot mutate stored data.

- [ ] **Step 4: Verify GREEN**

Run: `pytest tests/unit/test_conversation_repository.py -v`

Expected: PASS.

- [ ] **Step 5: Write the failing PostgreSQL mapping/migration test and verify RED**

Assert message ordering, `(conversation_id, sequence)` uniqueness, farmer/update index, and cascade deletion. Run: `pytest tests/integration/test_conversation_repository.py -v`. Expected: FAIL because mappings are absent.

- [ ] **Step 6: Implement SQLAlchemy rows, adapter, migration, exports, and bootstrap wiring**

Create `advisory_conversations` and `advisory_conversation_messages`, with cascade FK and required indexes. Select PostgreSQL only when database configuration exists, otherwise use in-memory storage.

- [ ] **Step 7: Verify GREEN and commit**

Run: `pytest tests/unit/test_conversation_repository.py tests/integration/test_conversation_repository.py -v`

Expected: PASS when the test database is available. Commit: `feat: persist advisory conversations`.

### Task 2: Contextual text interpretation

**Files:**
- Modify: `services/questionnaire.py`
- Test: `tests/unit/test_questionnaire.py`, `tests/unit/test_questionnaire_completion.py`
- Create: `tests/unit/test_questionnaire_conversations.py`

**Interfaces:** Add `QuestionnaireResult(conversation, step | None, ready_request | None)` and `start_conversation`, `receive_message`, and `complete_conversation`. A ready result contains a valid `MobileAdvisoryRequest`; otherwise it holds the one next `QuestionnaireStep`.

- [ ] **Step 1: Write failing intent tests**

Test that “My tomato leaves have yellow spots” is stored as a farmer question and asks for onset, and that the visible label `Start farming` routes exactly like its stable option ID.

- [ ] **Step 2: Verify RED**

Run: `pytest tests/unit/test_questionnaire_conversations.py -v`

Expected: FAIL because conversation-aware handling is absent.

- [ ] **Step 3: Implement deterministic intent and fact extraction**

Recognize option IDs/labels, then crop-problem, soil, planting, and start-farming free text. Extract only crop, symptoms, onset/stage, practice, and location facts; append exact farmer text and assistant prompts.

- [ ] **Step 4: Verify GREEN**

Run: `pytest tests/unit/test_questionnaire_conversations.py -v`

Expected: PASS.

- [ ] **Step 5: Write failing pending-context and readiness tests**

Test that a pending onset answer fills onset rather than becoming a new question; a new intent preserves history and resets only abandoned-intent facts; two conversations are isolated; and a complete crop problem emits a ready `MobileAdvisoryRequest`.

- [ ] **Step 6: Verify RED, implement semantics, and verify GREEN**

First run `pytest tests/unit/test_questionnaire_conversations.py -v`; expect failure. Accept text as expected-field data unless it clearly starts another intent. Reuse locality/passport facts, choose the first required missing field, and emit requests only when complete. Then run `pytest tests/unit/test_questionnaire.py tests/unit/test_questionnaire_completion.py tests/unit/test_questionnaire_conversations.py -v`; expect PASS.

- [ ] **Step 7: Commit**

Commit: `feat: interpret questionnaire messages contextually`.

### Task 3: Shared mobile recommendation execution

**Files:**
- Create: `services/mobile_advisory.py`
- Modify: `api/mobile.py`, `engine/bootstrap.py`, `api/app.py`
- Test: `tests/unit/test_mobile_advisory_service.py`, `tests/integrations/test_api.py`

**Interfaces:** `MobileAdvisoryService.advise(request: MobileAdvisoryRequest, principal_subject: str) -> Recommendation` performs the current direct-mobile flow. Both direct and ready questionnaire requests use it.

- [ ] **Step 1: Write failing shared-flow test**

Assert both direct and questionnaire-ready advice validate image ownership, apply analysis, add action/contact guidance, and format for the profile.

- [ ] **Step 2: Verify RED**

Run: `pytest tests/unit/test_mobile_advisory_service.py -v`

Expected: FAIL because the shared service is absent.

- [ ] **Step 3: Extract and wire the service**

Move existing `api/mobile.py` processing without changing its response contract; expose it through app state for questionnaire use.

- [ ] **Step 4: Verify GREEN and commit**

Run: `pytest tests/unit/test_mobile_advisory_service.py tests/integrations/test_api.py -v`

Expected: PASS. Commit: `refactor: share mobile advisory execution`.

### Task 4: Compatible API and additional history endpoint

**Files:**
- Modify: `api/questionnaire.py`, `docs/MOBILE_FRONTEND_API_HANDOFF.md`, `tests/integrations/test_questionnaire_api.py`
- Create: `tests/integrations/test_questionnaire_conversations_api.py`

**Interfaces:** Questionnaire payloads accept optional `conversation_id`. `start` returns `{complete, conversation_id, step}`; `answer` returns `{complete, conversation_id, step?, recommendation?}`; GET history returns `{conversation_id, status, context, messages, recommendation?}`.

- [ ] **Step 1: Write failing API tests**

Test start/free-text returning ID and next prompt; ready response returning recommendation; isolated histories; rejected foreign access; latest-open fallback; and clear `400` when no legacy conversation is open.

- [ ] **Step 2: Verify RED**

Run: `pytest tests/integrations/test_questionnaire_conversations_api.py -v`

Expected: FAIL because IDs, automatic completion, and GET history are absent.

- [ ] **Step 3: Implement the endpoint-compatible contract**

Load only owner conversations; when absent, choose only latest open conversation. Map `QuestionnaireResult` to documented fields, use `MobileAdvisoryService` when ready, preserve explicit `/complete`, and add protected GET history.

- [ ] **Step 4: Update handoff, verify GREEN, and commit**

Document ID storage/echoing, automatic completion, history retrieval, and legacy fallback. Run: `ruff check api services engine integrations tests && pytest tests/integrations/test_questionnaire_api.py tests/integrations/test_questionnaire_conversations_api.py -v`. Expected: PASS. Commit: `feat: expose advisory conversation history`.

### Task 5: End-to-end verification

**Files:** Modify only if verification exposes a regression.

- [ ] **Step 1: Apply the migration**

Run: `alembic upgrade head`

Expected: exit 0 with both conversation tables created.

- [ ] **Step 2: Run the full test suite**

Run: `pytest`

Expected: PASS; separately report a pre-existing unavailable test database if it blocks integration tests.

- [ ] **Step 3: Run static checks and inspect final state**

Run: `ruff check . && mypy && git diff --check && git status --short`

Expected: PASS with no whitespace errors and only intended changes.
