# Regional SMS Delivery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver manual and engine-triggered, strictly region-scoped SMS alerts to active Cameroon phone registrations without changing normal advisory recommendations.

**Architecture:** Add a small SMS administration domain that persists registrations, broadcasts, delivery attempts, and automatic-alert deduplication independently of the existing recommendation/SMS simulator flow. Route real delivery through a Tranzak gateway adapter selected by configuration, while keeping simulator support. A separate worker consumes explicitly scoped alert candidates from a safe engine/knowledge boundary; when no validated alert candidate is available it sends nothing.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic 2, SQLAlchemy 2, Alembic, PostgreSQL, Requests, Docker Compose, existing zero-build HTML dashboard, pytest.

**Spec:** `docs/superpowers/specs/2026-10-09-regional-sms-delivery-design.md`

## Global Constraints

- Preserve existing recommendation APIs and their behavior; SMS failures must never change advisory results.
- Do not implement OTP, verification, inbound replies, crop/farm details in SMS registration, or new agronomic rules.
- Store only registration phone number, canonical Cameroon region, active status, and lifecycle timestamps.
- Send automatic messages only from validated engine/knowledge alert candidates with an explicit individual, region, or Cameroon-wide scope.
- A message without explicit scope is skipped, never broadcast.
- Keep Tranzak secrets in `.env`; never return them through API/dashboard output or commit them.
- Retain the existing simulator and legacy SMS/notification endpoints until a compatibility test proves they remain usable.
- Default automatic check interval is 3600 seconds; no real WeatherAPI key or valid alert candidate means no weather broadcast.

## Review Focus

- A number entered as `6XXXXXXXX`, `2376XXXXXXXX`, or `+237 6XX XX XX XX` is normalized to one canonical `+237...` value, while an invalid/non-Cameroon number is rejected (Task 1).
- A Centre registration cannot be included in a South regional broadcast, even when identifiers or display values are similar (Task 3).
- A broadcast preview count must exactly equal the saved recipient set at submission time; inactive registrations are excluded (Task 4).
- A worker alert lacking explicit scope, valid knowledge provenance, or a new fingerprint results in zero delivery attempts (Task 7).
- A Tranzak network/authentication error becomes a safe failed delivery record and cannot cause a normal recommendation endpoint to fail (Task 5).

---

## File Structure

| Path | Responsibility |
| --- | --- |
| `engine/sms/phone.py` | Cameroon number normalization and canonical region validation. |
| `engine/sms/models.py` | Registration, scope, broadcast, delivery, and proactive-alert value objects. |
| `engine/interfaces/sms_admin.py` | Repository, delivery gateway, and alert-source protocols. |
| `integrations/database/sms_admin_repository.py` | PostgreSQL persistence for SMS registration, broadcast, delivery, deduplication, and settings. |
| `integrations/database/tables.py` | SQLAlchemy rows and indexes for the SMS administration tables. |
| `migrations/versions/<revision>_add_regional_sms_delivery.py` | Schema migration for the new tables/columns. |
| `integrations/sms/tranzak.py` | Token-aware Tranzak HTTP gateway; no business routing logic. |
| `integrations/sms/simulator/admin_gateway.py` | Deterministic gateway used by SMS administration tests and local runs. |
| `services/sms_delivery.py` | Registration lifecycle, preview, send routing, audit-safe history, and message sizing. |
| `services/proactive_alerts.py` | Validates engine/knowledge candidates, filters scope, and deduplicates automatic delivery. |
| `services/proactive_alert_source.py` | Read-only adapter from validated knowledge/engine to `ProactiveAlert`; returns no candidates until knowledge supports it. |
| `api/admin_sms.py` | Admin-only REST endpoints for registrations, manual broadcasts, deliveries, and automatic-alert settings. |
| `scripts/run_proactive_alerts.py` | One worker cycle callable by Docker and tests. |
| `dashboard/index.html` | Admin dashboard screens for registrations, manual SMS, automatic settings, and history. |
| `engine/config.py`, `engine/bootstrap.py`, `api/app.py`, `docker-compose.yml` | Configuration, composition, router registration, and worker deployment. |
| `tests/unit/test_sms_phone.py` | Number and region unit tests. |
| `tests/integration/test_sms_admin_repository.py` | Persistence/repository tests. |
| `tests/integrations/test_tranzak_gateway.py` | Mocked HTTP contract tests for Tranzak. |
| `tests/integrations/test_admin_sms_api.py` | Authenticated API, routing, preview, and compatibility tests. |
| `tests/unit/test_proactive_alerts.py` | Candidate validation, regional filtering, and deduplication tests. |
| `tests/integration/test_proactive_alert_worker.py` | One-cycle worker integration tests. |

### Task 1: SMS domain values and configuration

**Files:**
- Create: `engine/sms/__init__.py`
- Create: `engine/sms/phone.py`
- Create: `engine/sms/models.py`
- Create: `engine/interfaces/sms_admin.py`
- Modify: `engine/config.py`
- Modify: `engine/interfaces/__init__.py`
- Modify: `tests/test_config.py`
- Test: `tests/unit/test_sms_phone.py`

**Interfaces:**
- Produces `normalize_cameroon_phone(value: str) -> str`, `CameroonRegion`, `DeliveryScope`, `SMSRegistration`, `ManualBroadcast`, `ProactiveAlert`, `SMSAdminRepository`, `SMSDeliveryGateway`, and `ProactiveAlertSource`.
- Consumed by Tasks 2–7.

- [ ] **Step 1: Write failing normalization and configuration tests**

```python
def test_normalize_cameroon_phone_accepts_local_and_e164_forms() -> None:
    assert normalize_cameroon_phone("6 77 12 34 56") == "+237677123456"
    assert normalize_cameroon_phone("237677123456") == "+237677123456"

def test_normalize_cameroon_phone_rejects_invalid_input() -> None:
    with pytest.raises(ValueError, match="Cameroon"):
        normalize_cameroon_phone("+447700900123")

def test_settings_reads_tranzak_and_proactive_options(monkeypatch) -> None:
    monkeypatch.setenv("SMS_PROVIDER", "tranzak")
    monkeypatch.setenv("TRANZAK_APP_ID", "test-app")
    monkeypatch.setenv("PROACTIVE_SMS_INTERVAL_SECONDS", "3600")
    assert Settings.from_env().proactive_sms_interval_seconds == 3600
```

- [ ] **Step 2: Run unit tests to verify they fail**

Run: `pytest tests/unit/test_sms_phone.py tests/test_config.py -v`  
Expected: FAIL because the SMS domain values and configuration options do not exist.

- [ ] **Step 3: Implement canonical values and settings**

Create the exact functions/types above. Canonicalize the ten Cameroon regions in one controlled enum/value set. Add settings for `TRANZAK_APP_ID`, `TRANZAK_APP_KEY`, `TRANZAK_SENDER_ID`, `TRANZAK_BASE_URL`, `TRANZAK_TIMEOUT_SECONDS`, `PROACTIVE_SMS_ENABLED`, and `PROACTIVE_SMS_INTERVAL_SECONDS`; validate allowed provider names and positive timeout/interval values.

- [ ] **Step 4: Run unit tests to verify they pass**

Run: `pytest tests/unit/test_sms_phone.py tests/test_config.py -v`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add engine/sms engine/interfaces/sms_admin.py engine/interfaces/__init__.py engine/config.py tests/unit/test_sms_phone.py tests/test_config.py
git commit -m "feat: add regional SMS domain configuration"
```

### Task 2: Persistent registrations, deliveries, settings, and deduplication

**Files:**
- Modify: `integrations/database/tables.py`
- Create: `integrations/database/sms_admin_repository.py`
- Modify: `integrations/database/__init__.py`
- Create: `migrations/versions/<revision>_add_regional_sms_delivery.py`
- Test: `tests/integration/test_sms_admin_repository.py`

**Interfaces:**
- Consumes `SMSRegistration`, `ManualBroadcast`, `DeliveryScope`, and repository protocol from Task 1.
- Produces `PostgresSMSAdminRepository` with `create_registration`, `update_registration`, `list_registrations`, `delete_registration`, `resolve_active_recipients`, `create_delivery`, `list_deliveries`, `was_alert_delivered`, and automatic-settings methods.
- Consumed by Tasks 3, 4, 6, and 7.

- [ ] **Step 1: Write failing repository tests**

```python
def test_region_resolution_returns_only_active_exact_matches(repository) -> None:
    repository.create_registration(phone="+237677123456", region="South")
    repository.create_registration(phone="+237677123457", region="Centre")
    repository.create_registration(phone="+237677123458", region="South", active=False)
    assert [item.phone for item in repository.resolve_active_recipients(DeliveryScope.region("South"))] == ["+237677123456"]

def test_alert_fingerprint_is_retained_for_deduplication(repository) -> None:
    repository.create_delivery(..., alert_fingerprint="weather:south:2026-10-09")
    assert repository.was_alert_delivered("registration-id", "weather:south:2026-10-09") is True
```

- [ ] **Step 2: Run repository tests to verify they fail**

Run: `pytest tests/integration/test_sms_admin_repository.py -v`  
Expected: FAIL because the rows, repository, and migration do not exist.

- [ ] **Step 3: Add rows, migration, and repository implementation**

Add separate tables for registrations, broadcasts, and administration delivery attempts. Add an alert-fingerprint uniqueness/index strategy scoped to a registration. Preserve existing `sms_deliveries` and `PostgresSMSProvider` unchanged for legacy API compatibility. Implement transaction-safe recipient resolution at submission time and immutable delivery snapshots.

- [ ] **Step 4: Run migration and repository tests**

Run: `alembic upgrade head && pytest tests/integration/test_sms_admin_repository.py -v`  
Expected: migration succeeds and tests PASS against the configured test database.

- [ ] **Step 5: Commit**

```bash
git add integrations/database migrations/versions tests/integration/test_sms_admin_repository.py
git commit -m "feat: persist regional SMS registrations and deliveries"
```

### Task 3: Recipient routing and manual broadcast service

**Files:**
- Create: `services/sms_delivery.py`
- Create: `integrations/sms/simulator/admin_gateway.py`
- Test: `tests/unit/test_sms_delivery.py`

**Interfaces:**
- Consumes `SMSAdminRepository`, `SMSDeliveryGateway`, `Settings.sms_max_length`, and Task 1 values.
- Produces `SMSDeliveryService.preview_manual_broadcast(...) -> BroadcastPreview` and `SMSDeliveryService.send_manual_broadcast(...) -> BroadcastResult`.
- Consumed by Task 4.

- [ ] **Step 1: Write failing service tests**

```python
def test_preview_for_south_excludes_centre_and_inactive_registrations(service) -> None:
    preview = service.preview_manual_broadcast(message="Rain expected", scope=DeliveryScope.region("South"))
    assert preview.recipient_count == 1
    assert preview.region == "South"

def test_manual_broadcast_rejects_empty_recipient_set(service) -> None:
    with pytest.raises(ValueError, match="active registrations"):
        service.send_manual_broadcast(message="Hello", scope=DeliveryScope.region("North-West"))
```

- [ ] **Step 2: Run service tests to verify they fail**

Run: `pytest tests/unit/test_sms_delivery.py -v`  
Expected: FAIL because `SMSDeliveryService` does not exist.

- [ ] **Step 3: Implement routing and delivery recording**

Implement preview and submit as two separate operations. Re-resolve active recipients during submit, enforce the configured message length, record pending/sent/failed outcomes, and send each resolved normalized number through `SMSDeliveryGateway`. The simulator gateway returns deterministic accepted results for tests.

- [ ] **Step 4: Run service tests to verify they pass**

Run: `pytest tests/unit/test_sms_delivery.py -v`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add services/sms_delivery.py integrations/sms/simulator/admin_gateway.py tests/unit/test_sms_delivery.py
git commit -m "feat: route manual regional SMS broadcasts"
```

### Task 4: Admin API and dashboard controls

**Files:**
- Create: `api/admin_sms.py`
- Modify: `api/app.py`
- Modify: `api/admin.py`
- Modify: `dashboard/index.html`
- Test: `tests/integrations/test_admin_sms_api.py`

**Interfaces:**
- Consumes `SMSDeliveryService` from Task 3 and repository/settings from Task 2.
- Produces admin-only endpoints under `/api/v1/admin/sms` for registration CRUD, manual preview/send, delivery history, settings, and provider readiness.
- Consumed by the dashboard and Task 7 worker settings.

- [ ] **Step 1: Write failing authenticated API tests**

```python
def test_admin_can_register_number_preview_and_send_regional_broadcast(client, admin_headers) -> None:
    registration = client.post("/api/v1/admin/sms/registrations", headers=admin_headers, json={"phone": "677123456", "region": "South"})
    assert registration.status_code == 201
    preview = client.post("/api/v1/admin/sms/broadcasts/preview", headers=admin_headers, json={"message": "Alert", "scope": {"kind": "region", "region": "South"}})
    assert preview.json()["recipient_count"] == 1

def test_non_admin_cannot_view_phone_registrations(client, farmer_headers) -> None:
    assert client.get("/api/v1/admin/sms/registrations", headers=farmer_headers).status_code == 403
```

- [ ] **Step 2: Run API tests to verify they fail**

Run: `pytest tests/integrations/test_admin_sms_api.py -v`  
Expected: FAIL with 404 because the admin SMS router is absent.

- [ ] **Step 3: Implement API, container wiring, audit events, and dashboard sections**

Instantiate the repository/service only when persistence is configured; otherwise return an explicit 503 for administration routes. Add audit records for registration lifecycle, broadcast preview/submission, and automatic settings changes. Replace the dashboard’s old “SMS Simulator” panel with registrations, manual broadcast preview/send, automatic SMS settings, and delivery-history views. Keep legacy simulator pages and endpoints available separately.

- [ ] **Step 4: Run API and dashboard behavior tests**

Run: `pytest tests/integrations/test_admin_sms_api.py tests/integrations/test_sms_simulator.py -v`  
Expected: PASS; existing simulator tests remain green.

- [ ] **Step 5: Commit**

```bash
git add api/admin_sms.py api/app.py api/admin.py dashboard/index.html tests/integrations/test_admin_sms_api.py
git commit -m "feat: add admin regional SMS controls"
```

### Task 5: Tranzak delivery gateway

**Files:**
- Create: `integrations/sms/tranzak.py`
- Modify: `integrations/sms/__init__.py`
- Modify: `engine/bootstrap.py`
- Modify: `.env.example`
- Modify: `README.md`
- Test: `tests/integrations/test_tranzak_gateway.py`

**Interfaces:**
- Consumes Tranzak settings from Task 1 and `SMSDeliveryGateway` from Task 1.
- Produces `TranzakSMSGateway.send(phone: str, message: str) -> GatewayDeliveryResult`.
- Consumed by Task 3 and Task 7 through composition root selection.

- [ ] **Step 1: Write failing mocked HTTP tests**

```python
def test_gateway_gets_token_then_sends_to_normalized_phone(fake_session) -> None:
    fake_session.queue_json({"token": "token", "expiresIn": 3600})
    fake_session.queue_json({"status": "success", "reference": "provider-ref"})
    result = gateway.send("+237677123456", "Regional alert")
    assert result.provider_reference == "provider-ref"

def test_gateway_returns_safe_failure_when_token_request_times_out(fake_session) -> None:
    fake_session.queue_exception(requests.Timeout)
    assert gateway.send("+237677123456", "Alert").status == "failed"
```

- [ ] **Step 2: Run gateway tests to verify they fail**

Run: `pytest tests/integrations/test_tranzak_gateway.py -v`  
Expected: FAIL because the Tranzak adapter does not exist.

- [ ] **Step 3: Implement the gateway and provider readiness**

Use Requests with explicit timeouts, injecting a session constructor so tests can use the in-repository fake session instead of adding a new mocking dependency. Cache a token only until its safe expiry, then refresh it. Send only canonical phones and bounded messages. Convert provider/network failures into structured non-secret failure results rather than raising into application delivery loops. In `build_container`, select Tranzak only when `SMS_PROVIDER=tranzak` and all required settings are configured; otherwise select the simulator and expose a readiness reason.

- [ ] **Step 4: Run gateway and existing SMS compatibility tests**

Run: `pytest tests/integrations/test_tranzak_gateway.py tests/integrations/test_sms_simulator.py tests/integrations/test_api.py -v`  
Expected: PASS without real network calls.

- [ ] **Step 5: Commit**

```bash
git add integrations/sms/tranzak.py integrations/sms/__init__.py engine/bootstrap.py .env.example README.md tests/integrations/test_tranzak_gateway.py
git commit -m "feat: add Tranzak SMS gateway"
```

### Task 6: Safe engine/knowledge alert-candidate boundary

**Files:**
- Create: `services/proactive_alert_source.py`
- Modify: `engine/interfaces/sms_admin.py`
- Test: `tests/unit/test_proactive_alert_source.py`

**Interfaces:**
- Produces `KnowledgeBackedProactiveAlertSource.list_alerts(region: CameroonRegion) -> list[ProactiveAlert]`.
- `ProactiveAlert` must contain `message`, `scope`, `fingerprint`, `provenance`, and `validated=True`.
- Consumed by Task 7.

- [ ] **Step 1: Write failing alert-source tests**

```python
def test_source_returns_no_alert_when_validated_knowledge_has_no_proactive_entry(source) -> None:
    assert source.list_alerts(CameroonRegion.SOUTH) == []

def test_source_rejects_entry_without_region_scope_or_validation(source) -> None:
    assert source.list_alerts(CameroonRegion.SOUTH) == []
```

- [ ] **Step 2: Run source tests to verify they fail**

Run: `pytest tests/unit/test_proactive_alert_source.py -v`  
Expected: FAIL because the candidate source does not exist.

- [ ] **Step 3: Implement the read-only candidate adapter**

Read only explicit proactive-alert entries supplied by validated knowledge/engine adapters. Do not derive crop-specific advice from registration data and do not create a fallback/general message. Until validated proactive entries are present in `BASE_CONNAISSANCES_AGRICOLES`, return an empty list. Document the required future knowledge-entry shape in the adapter docstring and README.

- [ ] **Step 4: Run source tests to verify they pass**

Run: `pytest tests/unit/test_proactive_alert_source.py -v`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add services/proactive_alert_source.py engine/interfaces/sms_admin.py tests/unit/test_proactive_alert_source.py README.md
git commit -m "feat: add validated proactive alert boundary"
```

### Task 7: Proactive delivery orchestration and Docker worker

**Files:**
- Create: `services/proactive_alerts.py`
- Create: `scripts/run_proactive_alerts.py`
- Modify: `engine/bootstrap.py`
- Modify: `docker-compose.yml`
- Modify: `.env.example`
- Test: `tests/unit/test_proactive_alerts.py`
- Test: `tests/integration/test_proactive_alert_worker.py`

**Interfaces:**
- Consumes `ProactiveAlertSource` from Task 6 and `SMSDeliveryService` from Task 3.
- Produces `ProactiveAlertService.run_once() -> ProactiveRunSummary` and a single-cycle command-line script.

- [ ] **Step 1: Write failing orchestrator tests**

```python
def test_run_once_sends_south_alert_only_to_active_south_registrations(service) -> None:
    summary = service.run_once()
    assert summary.sent == 1
    assert gateway.sent_phones == ["+237677123456"]

def test_run_once_skips_duplicate_and_unscoped_alerts(service) -> None:
    summary = service.run_once()
    assert summary.sent == 0
    assert summary.skipped >= 2
```

- [ ] **Step 2: Run orchestrator tests to verify they fail**

Run: `pytest tests/unit/test_proactive_alerts.py tests/integration/test_proactive_alert_worker.py -v`  
Expected: FAIL because the proactive orchestrator and script do not exist.

- [ ] **Step 3: Implement one safe worker cycle**

Implement `run_once` as a bounded cycle: read automatic settings; stop when disabled; enumerate only regions with active registrations; obtain candidates; enforce validation and exact scope; deduplicate by registration/fingerprint; send through the delivery service; and return a non-secret summary. Add `proactive-alert-worker` Docker Compose service that repeatedly calls the single-cycle script using `PROACTIVE_SMS_INTERVAL_SECONDS`. Give it database, knowledge, SMS, WeatherAPI, and Tranzak environment variables, but no dashboard role.

- [ ] **Step 4: Run worker tests and Docker configuration validation**

Run: `pytest tests/unit/test_proactive_alerts.py tests/integration/test_proactive_alert_worker.py -v && docker compose config --quiet`  
Expected: PASS; Compose configuration validates.

- [ ] **Step 5: Commit**

```bash
git add services/proactive_alerts.py scripts/run_proactive_alerts.py engine/bootstrap.py docker-compose.yml .env.example tests/unit/test_proactive_alerts.py tests/integration/test_proactive_alert_worker.py
git commit -m "feat: run regional proactive SMS alerts"
```

### Task 8: End-to-end verification, retention, and operational documentation

**Files:**
- Modify: `services/retention.py`
- Modify: `tests/integration/test_media_privacy_and_uow.py`
- Modify: `README.md`
- Modify: `docs/TESTING.md`
- Modify: `docs/PRODUCTION_DEPLOYMENT.md`
- Test: `tests/integrations/test_admin_sms_api.py`

**Interfaces:**
- Consumes all earlier tasks.
- Produces documented deployment and operational checks for simulator, Tranzak, manual broadcasts, worker, and retention.

- [ ] **Step 1: Write failing retention and end-to-end tests**

```python
def test_retention_removes_expired_sms_admin_delivery_records(retention_service) -> None:
    assert retention_service.cleanup().sms_admin_deliveries == 1

def test_recommendation_succeeds_when_tranzak_gateway_fails(client) -> None:
    response = client.post("/api/v1/advisory/mobile", json=valid_mobile_request)
    assert response.status_code == 200
```

- [ ] **Step 2: Run targeted tests to verify they fail**

Run: `pytest tests/integration/test_media_privacy_and_uow.py tests/integrations/test_admin_sms_api.py -v`  
Expected: FAIL because new SMS administration records are not in retention and the isolation case is not pinned.

- [ ] **Step 3: Extend retention and write operational documentation**

Include the new delivery history table in existing SMS retention without deleting registrations. Document exact `.env` placeholders, how to select simulator vs Tranzak sandbox/production, how the admin dashboard manages numbers, and the fact that automatic delivery remains idle until validated region-scoped knowledge entries exist. Add no real credentials or real SMS send commands to tests/docs.

- [ ] **Step 4: Run the complete verification suite**

Run: `pytest -q && ruff check api engine integrations services tests && mypy api engine integrations services`  
Expected: all commands PASS. Then run `alembic upgrade head` against the local database and `docker compose config --quiet`.

- [ ] **Step 5: Commit**

```bash
git add services/retention.py tests/integration/test_media_privacy_and_uow.py README.md docs/TESTING.md docs/PRODUCTION_DEPLOYMENT.md
git commit -m "docs: complete regional SMS operations"
```

## Plan Self-Review

- **Spec coverage:** Tasks 1–2 implement validated registration/persistence; Tasks 3–4 manual dashboard controls and strict routing; Task 5 provider configuration and failure isolation; Tasks 6–7 safe automatic engine/knowledge delivery and deployment; Task 8 retention, documentation, and full verification.
- **No agronomy gap:** Task 6 deliberately returns no automatic candidates until knowledge contains validated, explicitly scoped entries. This respects the requirement not to invent agricultural recommendations while making the pipeline ready for future validated data and WeatherAPI availability.
- **Type consistency:** All routing passes `DeliveryScope`; all automated work passes `ProactiveAlert`; external sending uses `SMSDeliveryGateway`, avoiding changes to the legacy `SMSProvider` signature.
- **Safety coverage:** Every Review Focus item is directly pinned in Tasks 1, 3, 4, 5, and 7.
- **Proportion:** Tasks are split at independently testable boundaries: domain, persistence, routing, API/UI, gateway, alert source, worker, operations.
