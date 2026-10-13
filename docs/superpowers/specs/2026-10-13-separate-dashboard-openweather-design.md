# Separate Dashboard Deployment and OpenWeather Design

## Goal

Publish the administrative dashboard independently as a static GitHub Pages
site while keeping the deployable backend source on the `backend` branch.
The backend must use OpenWeatherMap after an operator supplies its API key.

## Confirmed requirements

- `backend` is the backend deployment branch and contains every project file
  except `dashboard/` and `BASE_CONNAISSANCES_AGRICOLES/`.
- `dashboard` is a static-only deployment branch for GitHub Pages.
- The dashboard must be removed from the backend source and the backend must
  no longer serve `/dashboard` or `/dashboard/sms-receiver`.
- `backend1` and `backendboth` are existing branches whose unique work must be
  included in `backend`.
- OpenWeatherMap replaces WeatherAPI as the configured live weather provider.
- Operators paste the secret only into the backend deployment environment;
  no API key is committed or exposed to the dashboard.

## Branch architecture

`backend` will be based on the current integrated backend history, then checked
against `backend1` and `backendboth` for commits that are not already
reachable. It retains all source, tests, operational files, documentation, and
configuration other than the two explicit exclusions.

`dashboard` will be an orphan-like static deployment branch containing only
the two HTML pages, a public `config.js` with the API base URL placeholder,
and GitHub Pages deployment configuration. It must not contain Python source,
backend environment files, provider secrets, or agricultural knowledge data.

## Backend removals and external knowledge

The backend deletes the `dashboard/` directory, `api/dashboard.py`, its router
registration, and tests/docs that claim the backend serves dashboard pages.
The application continues to expose its admin API endpoints.

`BASE_CONNAISSANCES_AGRICOLES/` is removed from the `backend` branch and is
ignored there. Deployments provide it separately (for example as a mounted
volume) and point `KNOWLEDGE_PATH` to the mounted location. Documentation and
Compose configuration explain this requirement; no agricultural data is
silently recreated.

## Dashboard runtime configuration

The HTML pages load `config.js` before their application scripts. It defines
`window.APP_CONFIG.API_BASE_URL`, a public URL such as
`https://api.example.org`. The dashboard prefixes all backend requests with
this value. Credentials remain the existing bearer token in browser storage;
the dashboard configuration contains no private key.

GitHub Pages publishes the `dashboard` branch root. The actual Pages URL is
listed in backend `CORS_ORIGINS` along with local development origins.

## OpenWeatherMap integration

Add an OpenWeatherMap adapter behind the existing weather provider boundary.
`WEATHER_PROVIDER=openweathermap` activates it and
`OPENWEATHERMAP_API_KEY` supplies its credential. Missing or invalid
credentials must produce the existing safe unavailable-provider behavior;
they must not prevent startup or appear in responses/logs. Remove the
WeatherAPI-specific configuration from committed examples and deployment
wiring.

## Verification

Tests prove the OpenWeatherMap configuration and adapter behavior, and prove
the backend no longer serves dashboard routes. Static dashboard checks prove
the public API base configuration is loaded and used. The backend test suite,
format/lint checks where configured, and a GitHub Pages build/configuration
check run before branch commits and push.

## Out of scope

- Supplying a real OpenWeatherMap API key.
- Hosting or copying the agricultural knowledge base.
- Changing the dashboard's visual features or backend admin API contract.
