# Contact Recommendation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automatically append safe, actionable specialist/vendor guidance to every mobile recommendation and provide verified-contact discovery plus administration.

**Architecture:** The canonical advisory engine and `RecommendationBuilder` stay untouched. A pure `ContactRecommendationService` classifies only the completed recommendation and already-produced evidence at the mobile API boundary, so contact routing is proactive and immediate without delaying or altering agricultural reasoning. A database-backed contact repository powers separate public discovery and admin management routes.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy, Alembic, PostgreSQL, pytest.

**Spec:** `docs/superpowers/specs/2026-10-07-contact-recommendation-design.md`

## Global Constraints

- Do not modify `AdvisoryEngine`, `RecommendationBuilder`, T1–T7 selection/evaluation, knowledge forest, or agricultural conclusions.
- Evaluate support after the canonical recommendation is generated, using only its existing output and image-evidence metadata.
- Every mobile recommendation response must contain a contact result, with neither flags selected when no support is indicated.
- Do not recommend a vendor merely because a matching vendor exists in persistence.
- Public contact discovery returns only `verified=true` and `active=true` records.
- Never initiate communication or expose farmer credentials, tokens, profile data, traces, or conversation history to a contact.
- Extend the existing `/api/v1/admin` router; do not create a second admin system.
- Keep persistence-backed routes unavailable with HTTP 503 if the application has no configured database.

## Review Focus

- An unfamiliar warning/action must produce neither flag, not an invented diagnosis or vendor suggestion (Task 1).
- The insufficient-evidence recommendation must require a specialist even when it has no matched candidate (Task 1).
- A matching but unverified or inactive contact must never leak from either public discovery endpoint (Task 4).
- A fully valid recommendation must still return normally if contact evaluation receives absent/empty visual evidence (Task 2).
- An active contact without a usable contact method must be rejected by admin validation (Task 5).

---

## File structure

- `engine/models/responses.py` — response contract additions only.
- `services/contact_recommendation.py` — pure post-recommendation evaluator and category mapping.
- `api/mobile.py` — invokes evaluator after engine output and before presentation adaptation.
- `integrations/database/tables.py` — contact ORM row and indexes.
- `integrations/database/contact_repository.py` — focused persistence CRUD/filtering/ranking.
- `migrations/versions/<revision>_add_agricultural_contacts.py` — schema upgrade/downgrade.
- `api/contacts.py` — authenticated public discovery endpoints.
- `api/admin.py` — protected contact management endpoints and audit writes.
- `api/app.py` — application services and router registration.
- `tests/unit/test_contact_recommendation.py` — classification contract.
- `tests/integration/test_contacts_api.py` — public discovery, admin lifecycle, persistence failure handling.

### Task 1: Define the contact-recommendation response and pure evaluator

**Files:**
- Modify: `engine/models/responses.py`
- Create: `services/contact_recommendation.py`
- Create: `tests/unit/test_contact_recommendation.py`

**Interfaces:**
- Consumes: `Recommendation` from `engine.models.responses` and `list[dict[str, object]]` visual evidence.
- Produces: `ContactRecommendation` and `ContactRecommendationService.evaluate(recommendation: Recommendation, visual_evidence: list[dict[str, object]]) -> ContactRecommendation`.

- [ ] **Step 1: Write failing evaluator contract tests**

```python
def test_unknown_recommendation_text_requires_no_contact() -> None:
    result = ContactRecommendationService().evaluate(recommendation, [])
    assert result.specialist_required is False
    assert result.vendor_required is False

def test_insufficient_evidence_requires_specialist() -> None:
    result = ContactRecommendationService().evaluate(insufficient_evidence_recommendation, [])
    assert result.specialist_category == "field_assessment"

def test_fertilizer_action_requires_fertilizer_vendor() -> None:
    result = ContactRecommendationService().evaluate(fertilizer_recommendation, [])
    assert result.vendor_category == "fertilizer"

def test_uncertain_disease_and_treatment_requires_both() -> None:
    result = ContactRecommendationService().evaluate(both_recommendation, [])
    assert result.specialist_required is True
    assert result.vendor_required is True
```

- [ ] **Step 2: Run the unit tests to verify they fail**

Run: `pytest tests/unit/test_contact_recommendation.py -v`

Expected: FAIL because the response model and evaluator do not exist.

- [ ] **Step 3: Add `ContactRecommendation` to `engine/models/responses.py`**

Define a `StrictModel` with `specialist_required`, `vendor_required`, nullable
`specialist_reason`, `vendor_reason`, `specialist_category`, and `vendor_category`.
Add `contact_recommendation: ContactRecommendation | None = None` to
`Recommendation`; do not change any existing field, builder, or trace contract.

- [ ] **Step 4: Implement `ContactRecommendationService.evaluate(...)`**

Use normalized text from primary/alternative names and summaries, actions, warnings,
uncertainty, and visual-evidence relevance/summary. Keep all category phrases in
one private immutable mapping. Return `field_assessment` for insufficient evidence,
`soil_analysis` for explicit lab/soil-test requests, `crop_disease` for explicit
disease confirmation, and a vendor category only for explicit input/equipment/service
phrases. The method is pure and makes no repository calls.

- [ ] **Step 5: Extend tests for missing visual evidence and stable recommendation data**

Assert an empty evidence list is accepted and `recommendation.model_dump()` is
identical before and after evaluation.

- [ ] **Step 6: Run unit tests to verify they pass**

Run: `pytest tests/unit/test_contact_recommendation.py -v`

Expected: PASS.

- [ ] **Step 7: Commit the response and evaluator**

```bash
git add engine/models/responses.py services/contact_recommendation.py tests/unit/test_contact_recommendation.py
git commit -m "feat: evaluate recommendation contact support"
```

### Task 2: Attach support guidance proactively to mobile recommendations

**Files:**
- Modify: `api/app.py`
- Modify: `api/mobile.py`
- Modify: `tests/integrations/test_api.py`

**Interfaces:**
- Consumes: `ContactRecommendationService.evaluate(...)` from Task 1.
- Produces: every successful `POST /api/v1/advisory/mobile` response has a
  non-null `contact_recommendation` object.

- [ ] **Step 1: Write a failing mobile endpoint test**

```python
def test_mobile_response_always_has_contact_recommendation(client, mobile_payload) -> None:
    response = client.post("/api/v1/advisory/mobile", json=mobile_payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["contact_recommendation"] == {
        "specialist_required": False,
        "vendor_required": False,
        "specialist_reason": None,
        "vendor_reason": None,
        "specialist_category": None,
        "vendor_category": None,
    }
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/integrations/test_api.py::test_mobile_response_always_has_contact_recommendation -v`

Expected: FAIL because the response currently has no contact result.

- [ ] **Step 3: Construct and register the service in `api/app.py`**

Set `app.state.contact_recommendation_service` to `ContactRecommendationService()`;
it has no database dependency and must be available in both in-memory and PostgreSQL
deployments.

- [ ] **Step 4: Evaluate after `container.engine.advise(...)` in `api/mobile.py`**

Call the service with the canonical recommendation and collected `visual_evidence`,
then use `recommendation.model_copy(update={...})` to attach the result before
`adapt_recommendation`. Preserve the existing owner/media/image validation order and
the normal recommendation response on every outcome.

- [ ] **Step 5: Add specialist, vendor, both, and visual-evidence integration assertions**

Cover representative existing recommendation fixtures. Assert primary, actions,
warnings, and trace ID still match the pre-contact recommendation data.

- [ ] **Step 6: Run endpoint and evaluator regression tests**

Run: `pytest tests/integrations/test_api.py tests/unit/test_contact_recommendation.py -v`

Expected: PASS.

- [ ] **Step 7: Commit proactive response integration**

```bash
git add api/app.py api/mobile.py tests/integrations/test_api.py
git commit -m "feat: include contact guidance in mobile advisory"
```

### Task 3: Add contact persistence and migration

**Files:**
- Modify: `integrations/database/tables.py`
- Create: `integrations/database/contact_repository.py`
- Modify: `integrations/database/__init__.py`
- Create: `migrations/versions/<revision>_add_agricultural_contacts.py`
- Create: `tests/integration/test_contact_repository.py`

**Interfaces:**
- Produces: `AgriculturalContactRow`, `AgriculturalContactRepository`, and methods
  `create`, `get`, `update`, `set_verified`, `set_active`, and
  `find_public(contact_type, category, crop_id, region, location)`.
- Consumes: SQLAlchemy `sessionmaker` and contact request/domain models defined in Task 4.

- [ ] **Step 1: Write failing repository tests using the project database fixture**

```python
def test_find_public_excludes_unverified_and_inactive_contacts(repository) -> None:
    results = repository.find_public("VENDOR", "fertilizer", "tomato", "Centre", None)
    assert [contact.name for contact in results] == ["Verified fertilizer vendor"]
```

- [ ] **Step 2: Run repository tests to verify they fail**

Run: `pytest tests/integration/test_contact_repository.py -v`

Expected: FAIL because the contact table and repository are absent.

- [ ] **Step 3: Add `AgriculturalContactRow` and its migration**

Use `agricultural_contacts`, string `contact_id` primary key, JSON document
`crop_ids`, nullable communication/location fields, boolean `verified`/`active`
defaulting false, timestamp fields, and indexes on `(contact_type, category)`,
`region`, and `(verified, active, contact_type)`. Write matching Alembic upgrade
and downgrade operations.

- [ ] **Step 4: Implement `AgriculturalContactRepository`**

Rank public matches by exact category, membership in `crop_ids`, exact region,
exact location, then normalized name. Apply verified/active/type restrictions in
the SQL query before ranking. Keep administrative lookup separate so it can see
all status values.

- [ ] **Step 5: Add repository lifecycle and ranking tests**

Cover create/update/get, category/crop/region precedence, empty optional contact
methods, and no results when only untrusted records match.

- [ ] **Step 6: Run repository tests**

Run: `pytest tests/integration/test_contact_repository.py -v`

Expected: PASS.

- [ ] **Step 7: Commit persistence support**

```bash
git add integrations/database/tables.py integrations/database/contact_repository.py integrations/database/__init__.py migrations/versions tests/integration/test_contact_repository.py
git commit -m "feat: persist agricultural contacts"
```

### Task 4: Expose authenticated verified-contact discovery

**Files:**
- Create: `api/contacts.py`
- Modify: `api/app.py`
- Modify: `api/dependencies.py`
- Modify: `tests/integration/test_contacts_api.py`

**Interfaces:**
- Consumes: `AgriculturalContactRepository.find_public(...)` from Task 3 and the
  existing principal dependency.
- Produces: `GET /api/v1/contacts/specialists` and `/vendors` contact-card responses.

- [ ] **Step 1: Write failing public endpoint tests**

```python
def test_vendor_lookup_returns_only_relevant_verified_active_cards(client, auth_headers) -> None:
    response = client.get(
        "/api/v1/contacts/vendors?category=fertilizer&crop_id=tomato&region=Centre",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["items"] == [{"name": "Verified fertilizer vendor", ...}]
    assert "verified" not in response.json()["items"][0]
```

- [ ] **Step 2: Run public endpoint tests to verify they fail**

Run: `pytest tests/integration/test_contacts_api.py::test_vendor_lookup_returns_only_relevant_verified_active_cards -v`

Expected: FAIL because the router is absent.

- [ ] **Step 3: Define query and public-card Pydantic models in `api/contacts.py`**

Accept only `category`, `crop_id`, `region`, and `location`; return a card with
name, description, specialization/category, location/region/address, and non-null
phone/WhatsApp/email values. Do not return ID, active/verified flags, timestamps,
or administrative notes.

- [ ] **Step 4: Implement both endpoints and persistence-unavailable handling**

Require the existing authenticated principal, route endpoint type to the repository,
and return 503 with the established persistence message when `container.database`
is absent. Register the router in `api/app.py`.

- [ ] **Step 5: Add endpoint tests for specialist type isolation and 503 mode**

Assert vendor records cannot appear in specialist results, invalid filters return
422, and an in-memory app returns 503 rather than unsafe fake contact data.

- [ ] **Step 6: Run public contact API tests**

Run: `pytest tests/integration/test_contacts_api.py -v`

Expected: PASS.

- [ ] **Step 7: Commit public discovery**

```bash
git add api/contacts.py api/app.py api/dependencies.py tests/integration/test_contacts_api.py
git commit -m "feat: expose verified agricultural contacts"
```

### Task 5: Extend the admin API with contact lifecycle management

**Files:**
- Modify: `api/admin.py`
- Modify: `api/app.py`
- Modify: `tests/integration/test_contacts_api.py`

**Interfaces:**
- Consumes: repository lifecycle methods from Task 3 and `app.state.audit_service`.
- Produces: admin contact list, create, get, patch, verification, and activation endpoints.

- [ ] **Step 1: Write failing admin lifecycle and authorization tests**

```python
def test_admin_can_verify_and_activate_contact_and_public_lookup_updates(client, admin_headers) -> None:
    contact = client.post("/api/v1/admin/contacts", json=payload, headers=admin_headers).json()
    client.post(f"/api/v1/admin/contacts/{contact['contact_id']}/verification", json={"verified": True}, headers=admin_headers)
    response = client.post(f"/api/v1/admin/contacts/{contact['contact_id']}/activation", json={"active": True}, headers=admin_headers)
    assert response.status_code == 200

def test_active_contact_requires_contact_method(client, admin_headers) -> None:
    assert response.status_code == 422
```

- [ ] **Step 2: Run targeted admin tests to verify they fail**

Run: `pytest tests/integration/test_contacts_api.py -k 'admin or active_contact' -v`

Expected: FAIL because contact administration endpoints are absent.

- [ ] **Step 3: Add admin request/response models and list endpoint**

Define create/patch models with email validation and normalized phone/WhatsApp
validation, a status request with a required boolean, and an all-status list query:
`type`, `category`, `region`, `verified`, `active`, `query`. Use `AdminDependency`
for every `/api/v1/admin/contacts` route.

- [ ] **Step 4: Implement CRUD and state transition routes in `api/admin.py`**

Implement `GET /contacts`, `POST /contacts`, `GET /contacts/{contact_id}`,
`PATCH /contacts/{contact_id}`, `POST /contacts/{contact_id}/verification`, and
`POST /contacts/{contact_id}/activation`. Reject activation if phone, WhatsApp, and
email are all absent. Emit one `AuditService.record(...)` event per successful
mutation with action, resource type `agricultural_contact`, ID, and changed field
names only.

- [ ] **Step 5: Extend tests for update/filter/audit/404 behaviour**

Assert non-admin requests are rejected, filters include unverified/inactive records
only for admin, nonexistent IDs return 404, editing methods changes the public card,
and audit data contains no communication value or secret.

- [ ] **Step 6: Run admin and public contact test suite**

Run: `pytest tests/integration/test_contacts_api.py tests/integration/test_contact_repository.py -v`

Expected: PASS.

- [ ] **Step 7: Commit admin management**

```bash
git add api/admin.py api/app.py tests/integration/test_contacts_api.py
git commit -m "feat: manage agricultural contacts in admin api"
```

### Task 6: Run complete verification and document the client contract

**Files:**
- Modify: `README.md`
- Modify: `docs/VALIDATION_REPORT.md`
- Test: `tests/unit/test_contact_recommendation.py`
- Test: `tests/integration/test_api.py`
- Test: `tests/integration/test_contact_repository.py`
- Test: `tests/integration/test_contacts_api.py`

**Interfaces:**
- Consumes: all completed task interfaces.
- Produces: documented mobile response and contact/admin APIs with verified test evidence.

- [ ] **Step 1: Add failing documentation-contract test only if the project has OpenAPI snapshot coverage**

If no such coverage exists, do not add a new snapshot mechanism; validate through
the integration tests below.

- [ ] **Step 2: Document the mobile `contact_recommendation` object and contact endpoints**

Include the four flag cases, public verified/active guarantee, category filters,
admin lifecycle routes, contact method visibility rule, no-auto-contact privacy
guarantee, and an explicit note that Flutter is an external client responsible for
rendering buttons from the response.

- [ ] **Step 3: Run targeted feature verification**

Run: `pytest tests/unit/test_contact_recommendation.py tests/integrations/test_api.py tests/integration/test_contact_repository.py tests/integration/test_contacts_api.py -v`

Expected: PASS.

- [ ] **Step 4: Run repository quality checks**

Run: `uv run ruff check . && uv run mypy engine api services integrations && uv run pytest`

Expected: all checks PASS.

- [ ] **Step 5: Update `docs/VALIDATION_REPORT.md` with actual command results**

Record the date, commands, pass counts, and explicit confirmation that normal
agricultural recommendation fields remain unchanged in the no-support case.

- [ ] **Step 6: Commit documentation and validation evidence**

```bash
git add README.md docs/VALIDATION_REPORT.md
git commit -m "docs: describe contact recommendation support"
```
