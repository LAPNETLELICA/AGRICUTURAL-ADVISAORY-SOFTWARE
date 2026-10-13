# Three-Pillar Repository Organization Plan

> Historical planning record recovered from the feature branch. The main checkout is now the canonical tree; this plan is retained for context and is not an instruction to restore retired folders.

**Goal:** Organize the repository around `engine/`, `BASE_CONNAISSANCES_AGRICOLES/`, and `integrations/` while preserving behavior and compatible interfaces.

**Architecture:** `engine/` owns deterministic reasoning, the Cameroon base owns the agricultural facts, and `integrations/` owns provider and database adapters. API, services, scripts, tests, and docs remain supporting folders.

## Preservation constraints

- Keep `BASE_CONNAISSANCES_AGRICOLES/` as the sole canonical agricultural source.
- Preserve user-facing compatibility through forwarding modules where needed.
- Keep generated/runtime directories out of source ownership areas.
- Do not change agronomic rules, facts, thresholds, or output behavior during organizational changes.

## Work items

- Maintain an organization map and validate required paths.
- Keep active runtime references on the Cameroon knowledge provider; retain only explicitly documented legacy references.
- Preserve language formatter compatibility through the forwarding `languages/` package and canonical `integrations/presentation/` implementation.
- Run import checks, structure validation, focused tests, Ruff, and the complete suite after structural edits.