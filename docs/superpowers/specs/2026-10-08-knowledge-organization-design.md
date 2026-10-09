# Knowledge Base and Repository Organization Design

> Historical design record recovered from the feature branch. The active project uses the current three-pillar layout described below; this document does not authorize restoring retired directories.

## Goal

Make `BASE_CONNAISSANCES_AGRICOLES/` the documented canonical agricultural
knowledge base and organize code by responsibility while preserving public APIs,
compatibility imports, and current behavior.

## Canonical structure

- `BASE_CONNAISSANCES_AGRICOLES/`: canonical Cameroon agricultural data.
- `engine/`: deterministic agricultural reasoning.
- `integrations/`: database, presentation, knowledge, storage, speech, translation,
  and weather adapters.
- `api/`: HTTP routes and security dependencies.
- `services/`: application workflows.
- `migrations/`, `scripts/`, `tests/`, and `docs/`: supporting project areas.

## Migration rules

- Runtime knowledge defaults to `BASE_CONNAISSANCES_AGRICOLES/`.
- `CameroonKnowledgeProvider` remains the canonical provider.
- `languages/` is a compatibility package forwarding formatter exports to
  `integrations/presentation/`; it must not contain a second formatter implementation.
- Generated artifacts, caches, coverage reports, virtual environments, and runtime
  data are excluded from source reorganization.
- Retired `knowledge/` and `backend2/` directories remain absent.

## Validation

Run structure validation, knowledge-provider tests, import checks, API tests,
migration graph validation, and repository-wide reference scans. Acceptance requires
one canonical agricultural knowledge root and functioning compatibility imports.