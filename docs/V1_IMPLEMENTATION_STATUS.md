# AgriSense V1 completion pass

This completion pass is scoped to V1 plus the explicitly requested SMS sandbox. It keeps the
reasoning engine provider-neutral and does not invent validated agronomy.

## Added in this pass

- Local bearer authentication with PBKDF2 password hashing, signed expiring tokens, farmer/admin
  roles, and ownership checks on advisory, recommendation and SMS inbox resources. Production can
  enforce authentication with `AUTH_REQUIRED=true`.
- A built-in management dashboard at `/dashboard` with overview, provider readiness, knowledge
  upload, education preview and SMS simulator sections.
- No-code knowledge import. The dashboard reads a JSON file, the backend validates a complete copy
  of the knowledge forest with the existing Pydantic contracts, then atomically installs and reloads
  the document only when validation succeeds.
- FR-14 education API at `/api/v1/education/...`. It derives lessons from the same crop profile and
  T1-T7 rule forest, organized as seven criteria: crop profile/care, soil care, region, topography,
  weather/climate, cultivation timing, and practices/risks.
- Proactive SMS sandbox subscriptions and a manual trigger endpoint. Each notification is generated
  by the existing advisory engine, formatted for SMS, translated only through the configured
  translation boundary, re-limited after translation, and delivered through the existing SMS
  provider abstraction.
- Android/Wi-Fi simulation receiver at `/dashboard/sms-receiver`. On a development LAN, open this
  URL from an Android phone using the computer's LAN address, enter the same recipient ID and the
  phone polls the virtual SMS inbox.
- Provider configuration placeholders for weather, translation, TTS and SMS. Translation, speech
  and SMS are now injectable in the composition root just like weather, so real adapters can be
  added without changing the deterministic advisory engine.
- Voice preparation endpoint `/api/v1/advisory/voice`. It returns the formatted text and a safe
  `audio_available=false` fallback while no TTS adapter is configured; a future injected adapter can
  supply audio without changing the endpoint contract.
- Readiness endpoint `/api/v1/ready` that separates process health from database/knowledge readiness.
- T7 selection correction: empty structural past data no longer selects T7 by itself.

## Intentionally not fabricated

The source audit states that all current crop profiles/rules are draft and that production must have
agronomist-approved, sourced, versioned knowledge. This implementation does **not** relabel draft
content as validated. Production remains no-go until at least one pilot crop receives real agronomy
signoff and regression boundaries.

Real weather, translation, TTS and SMS gateways are also not implemented because provider APIs and
credentials were explicitly not available. Their contracts, settings, injection points and safe
fallbacks are prepared.

## Development login

For development only, when `ADMIN_PASSWORD` is not set, the app bootstraps:

- username: `admin`
- password: `change-me-now`

Production must set `AUTH_SECRET`, `ADMIN_USERNAME`, `ADMIN_PASSWORD` and enable HTTPS at ingress.
Never use the development password outside a local sandbox.

## Useful endpoints

- `/dashboard`
- `/dashboard/sms-receiver`
- `/api/v1/auth/login`
- `/api/v1/education/crops/{crop_id}`
- `/api/v1/admin/knowledge/import`
- `/api/v1/notifications/subscriptions`
- `/api/v1/notifications/trigger/{recipient_id}`
- `/api/v1/advisory/voice`
- `/api/v1/ready`

## External release blockers

1. Agronomist validation/signoff for a canonical pilot crop and rule boundaries.
2. Real HTTPS ingress/TLS certificates and deployment secrets.
3. Real provider selection/credentials for weather, translation/TTS and SMS where product scope
   requires them.
4. Privacy/retention policy approval and controlled media storage if image evidence is enabled.
5. Production PostgreSQL integration/backup/restore drill in the target infrastructure.

## Production-hardening pass (latest)

The following previously open V1 production items are now implemented in code/configuration:

- HTTPS/TLS production ingress using a Caddy production profile, automatic certificate renewal,
  HTTP-to-HTTPS behavior and security headers.
- Controlled image-evidence upload/read/delete with private object-storage abstraction, local private
  V1 adapter, content-signature/type/size validation, authenticated ownership checks and expiry.
- Farmer privacy endpoints for retention summary, data export and deletion, plus configurable data
  retention and a daily production retention worker.
- PostgreSQL atomic advisory persistence through a shared UnitOfWork transaction across trace,
  recommendation, passport update and history write.
- Direct farmer ownership columns for new trace/recommendation/SMS persistence to make privacy
  export/deletion reliable without guessing IDs.
- Alembic migration for media/audit tables and ownership columns; readiness now checks the expected
  migration revision.
- Daily custom-format PostgreSQL backups with SHA-256 checksums and a restore script/drill procedure.
- New regression tests for controlled media, ownership, privacy account invalidation, readiness and
  transaction rollback. Existing behavior remains covered by the prior test suite.

The external Weather, Translation, TTS and real SMS provider APIs remain intentionally pluggable and
unconfigured until provider choices/credentials are supplied.
