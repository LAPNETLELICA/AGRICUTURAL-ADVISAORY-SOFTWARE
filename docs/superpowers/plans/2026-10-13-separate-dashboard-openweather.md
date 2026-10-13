# Separate Dashboard and OpenWeather Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish all backend files except the dashboard and agricultural knowledge on `backend`, publish a static dashboard on `dashboard`, and use OpenWeatherMap.

**Architecture:** Consolidate `backend1`, `backendboth`, and the current integrated backend history. Remove only the two excluded directories from `backend`. The static dashboard gets its API origin from public `config.js`; the backend uses an OpenWeatherMap adapter behind its existing weather provider interface.

**Tech Stack:** Python, FastAPI, Requests, pytest, HTML/JavaScript, GitHub Pages, Git.

**Spec:** `docs/superpowers/specs/2026-10-13-separate-dashboard-openweather-design.md`

## Global Constraints

- `backend` contains every project path except `dashboard/` and `BASE_CONNAISSANCES_AGRICOLES/`.
- `dashboard` contains static assets only; it never includes source code, knowledge data, `.env`, or secrets.
- The only weather settings are `WEATHER_PROVIDER=openweathermap` and `OPENWEATHERMAP_API_KEY`.
- An external mount supplies `KNOWLEDGE_PATH` in deployment.

## Review Focus

- Placeholder weather credentials make no external request.
- HTTP/payload failures never leak the API key.
- Dashboard URLs have exactly one separator slash.
- An unset dashboard API base reports an error rather than calling the Pages origin.
- The final backend manifest has neither excluded prefix.

---

### Task 1: Replace the WeatherAPI integration

**Files:** Create `integrations/weather/openweathermap.py`; modify `engine/config.py`, `engine/bootstrap.py`, `tests/test_config.py`, `tests/integrations/test_live_provider_adapters.py`; delete `integrations/weather/weatherapi.py`.

**Interfaces:** Produces `OpenWeatherMapProvider(api_key: str, *, timeout_seconds: float = 8.0)` with the existing `get_current` and `get_forecast` normalized result interface.

- [ ] **Step 1: Write failing tests**

Test `OPENWEATHERMAP_API_KEY` loading, `WEATHER_PROVIDER=openweathermap` selection, placeholder-key fallback, Cameroon location parameters, response mapping, and request errors.

- [ ] **Step 2: Verify red**

Run `pytest tests/test_config.py tests/integrations/test_live_provider_adapters.py -v`; expect missing OpenWeatherMap configuration/provider failures.

- [ ] **Step 3: Implement minimally**

Call OpenWeatherMap current and forecast endpoints, validate sample/empty keys before calling them, map required fields to existing weather keys, and translate request/payload errors to `ProviderUnavailableError`. Remove all WeatherAPI-specific selection and configuration.

- [ ] **Step 4: Verify green and commit**

Run the targeted test command, then commit `feat: use OpenWeatherMap weather provider`.

### Task 2: Make static dashboard API access configurable

**Files:** Create `dashboard/config.js`, `tests/unit/test_dashboard_deployment.py`; modify `dashboard/index.html`, `dashboard/receiver.html`.

**Interfaces:** `window.APP_CONFIG.API_BASE_URL` and shared `apiUrl(path: string): string` used by all dashboard requests.

- [ ] **Step 1: Write failing static asset tests**

Assert both HTML pages load `config.js`, dashboard API paths use a shared base URL helper, and configuration contains a public API-origin placeholder but no credential.

- [ ] **Step 2: Verify red**

Run `pytest tests/unit/test_dashboard_deployment.py -v`; expect missing configuration/helper failures.

- [ ] **Step 3: Implement minimally**

Add `window.APP_CONFIG = { API_BASE_URL: "https://api.example.org" }`, load it before page scripts, validate/normalize the public origin, and pass every API request through the helper.

- [ ] **Step 4: Verify green and commit**

Run the dashboard test, then commit `feat: configure dashboard API endpoint`.

### Task 3: Detach dashboard serving from FastAPI

**Files:** Delete `api/dashboard.py`, `tests/unit/test_dashboard_sms_page.py`; modify `api/app.py`, `README.md`; create `tests/integrations/test_dashboard_removed.py`.

**Interfaces:** `create_app()` no longer registers dashboard routes; all JSON admin API routes remain registered.

- [ ] **Step 1: Write failing route tests**

Assert `GET /dashboard` and `GET /dashboard/sms-receiver` return 404 while `/api/v1/health` and an existing authenticated admin API route retain their behavior.

- [ ] **Step 2: Verify red**

Run `pytest tests/integrations/test_dashboard_removed.py -v`; expect 200 responses from the still-registered dashboard routes.

- [ ] **Step 3: Implement minimally**

Remove the dashboard import/registration and its page-serving module/tests; replace README local dashboard instructions with separately hosted dashboard guidance.

- [ ] **Step 4: Verify green and commit**

Run `pytest tests/integrations/test_dashboard_removed.py tests/integrations/test_admin_sms_api.py -v`, then commit `refactor: detach dashboard from backend API`.

### Task 4: Document backend deployment requirements

**Files:** Modify `.env.example`, `docker-compose.yml`, `.gitignore`, `README.md`, `docs/PRODUCTION_DEPLOYMENT.md`, `tests/test_config.py`.

**Interfaces:** Deployment accepts `OPENWEATHERMAP_API_KEY`, external `KNOWLEDGE_PATH`, and configured Pages URL in `CORS_ORIGINS`.

- [ ] **Step 1: Write failing configuration checks**

Test the committed environment example/configuration for OpenWeatherMap-only keys and assert Compose forwards the key to weather consumers. Assert documentation states the external knowledge mount and CORS requirement.

- [ ] **Step 2: Verify red**

Run `pytest tests/test_config.py -v`; expect WeatherAPI remnants to violate the test.

- [ ] **Step 3: Implement minimally**

Replace WeatherAPI settings and Docker environment wiring, add the two exclusions to `.gitignore`, and document external knowledge provisioning and dashboard CORS.

- [ ] **Step 4: Verify green and commit**

Run `docker compose config && pytest tests/test_config.py -v`, then commit `docs: configure external knowledge and OpenWeatherMap`.

### Task 5: Build, verify, and publish deployment branches

**Files:** Delete `dashboard/` and `BASE_CONNAISSANCES_AGRICOLES/` only from `backend`; create root static assets, `.nojekyll`, and `README.md` only on `dashboard`.

**Interfaces:** `backend` receives the consolidated history; `dashboard` provides root-level GitHub Pages assets.

- [ ] **Step 1: Consolidate histories**

Compare each branch to the candidate with merge-base/log, merge or cherry-pick each unique `backend1` and `backendboth` commit, and resolve conflicts while preserving every non-excluded path.

- [ ] **Step 2: Verify the candidate manifest**

Run `git ls-tree -r --name-only HEAD`; ensure all expected project source, deployment, test, and documentation paths exist before exclusions.

- [ ] **Step 3: Create deployment branches**

Advance `backend` to the verified candidate; remove only its tracked `dashboard/` and `BASE_CONNAISSANCES_AGRICOLES/` paths. Create an orphan `dashboard` branch that contains only static dashboard assets, config, Pages marker, and deployment README.

- [ ] **Step 4: Verify manifests and full backend behavior**

Run `git ls-tree -r --name-only backend`, `git ls-tree -r --name-only dashboard`, `pytest`, and `docker compose config`. Confirm the backend exclusions and dashboard-only manifest.

- [ ] **Step 5: Commit and push**

Commit the branch changes, then run `git push origin backend dashboard`. If network is unavailable, retain local commits and report the exact command to retry.
