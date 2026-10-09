# Repository Organization Map

The backend has three primary pillars. They are the only locations for
agricultural facts, advisory reasoning, and external adapters.

| Area | Responsibility | Canonical location |
| --- | --- | --- |
| Agricultural knowledge | Cameroon crops, soils, regions, climate, calendars, risks, and practices | `BASE_CONNAISSANCES_AGRICOLES/` |
| Advisory reasoning | Deterministic context building, rule evaluation, constraints, ranking, and recommendation contracts | `engine/` |
| System adapters | Knowledge bridge, database, storage, weather, SMS, translation, and speech providers | `integrations/` |
| API boundary | HTTP routes, authentication, validation, and dashboard delivery | `api/` |
| Application services | Orchestration for education, notifications, privacy, media, technical fiches, and presentation | `services/` |
| Operations | Validation, smoke checks, retention, backup, and restore utilities | `scripts/` |
| Database evolution | Alembic migration history | `migrations/` |
| Verification | Unit, engine, rules, integration, and scenario tests | `tests/` |
| Documentation | Architecture, deployment, operational guides, and validation records | `docs/` |

## Knowledge boundary

`BASE_CONNAISSANCES_AGRICOLES/` is the sole canonical source of agricultural
content. `integrations/cameroon_knowledge.py` is the bridge that converts its
documents into the provider contracts consumed by `engine/`. The API and services
must obtain agricultural content through the application container, never by
creating another knowledge folder or embedding agronomic thresholds.

## Retired locations

The former `knowledge/` and `backend2/` directories were intentionally removed by
the project owner and must not be restored. Structure validation rejects them so
they cannot become competing sources of truth. The `languages/` package remains as
a compatibility layer that forwards formatter exports to `integrations/presentation/`.
Formatter implementation stays canonical in `integrations/presentation/`; do not
duplicate it under `languages/`.

## Deployment setting

The standard runtime setting is:

```dotenv
KNOWLEDGE_PATH=BASE_CONNAISSANCES_AGRICOLES
```

This path is used by `engine.config.Settings`, Docker, Compose, and the example
environment file. It may be overridden only to point to another complete,
compatible Cameroon knowledge-base release.
