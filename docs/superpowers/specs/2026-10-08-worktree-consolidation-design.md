# Worktree Consolidation Design

## Goal

Consolidate useful contact, specialist, vendor, and action-guidance work from
`.worktrees/contact-recommendation/` into the main backend checkout. The main
checkout becomes the sole working project tree while retaining every required
function, including the existing `languages/` interface.

## Canonical main structure

The active project remains organized around:

- `engine/` for deterministic advisory reasoning.
- `BASE_CONNAISSANCES_AGRICOLES/` for the sole agricultural source data.
- `integrations/` for database, provider, presentation, and knowledge adapters.

`api/`, `services/`, `migrations/`, `scripts/`, `tests/`, and `docs/` remain
supporting folders in the main checkout. The worktree is a source for comparison
only; it must not become a second runnable project.

## Preserve language functionality

The main checkout keeps a `languages/` compatibility package. Its public exports
(`MobileFormatter`, `SMSFormatter`, and `VoiceFormatter`) forward to the canonical
`integrations.presentation` implementation. Existing callers using
`from languages import ...` continue working, while all new internal imports use
`integrations.presentation`.

This retains the language feature without creating two formatter implementations.

## Worktree intake

The following worktree-only modules are candidates to merge into main after their
interfaces are checked against the current Cameroon-base architecture:

- `api/contacts.py`
- `services/contact_recommendation.py`
- `services/action_guidance.py`
- `integrations/database/contact_repository.py`
- `migrations/versions/e1a3b6d9f2c4_add_agricultural_contacts.py`
- their focused integration and unit tests
- the associated Groq/Fish Audio design and implementation-plan documents

Files present in both trees are merged by responsibility, never overwritten as a
whole file. In particular, the current main version remains authoritative for the
Cameroon knowledge provider, deployment configuration, repository organization,
and existing user changes.

## Retired and generated content

The retired `knowledge/` and `backend2/` directories remain absent. The old
`integrations/knowledge.py` JSON provider is not restored because it would create
a second knowledge source. Generated artifacts, `.git` metadata, caches, coverage
reports, virtual environments, and runtime data are never copied from the worktree.

## Validation

Validation will include import checks for both `languages` and
`integrations.presentation`, contact/action-guidance unit and integration tests,
Cameroon knowledge-provider tests, database migration checks, structure validation,
and the relevant API tests. A reference scan must show exactly one canonical
agricultural knowledge root.
