# V1 Production Hardening Report

Implemented on top of the previously completed V1 package without replacing the crop-centered T1-T7 inference architecture.

## Implemented

- HTTPS/TLS deployment profile using Caddy, automatic certificate lifecycle, reverse proxying, HSTS and security headers.
- Private controlled image-evidence storage boundary with authenticated upload/read/delete, ownership enforcement, JPEG/PNG/WebP signature validation, configurable size limit, random object keys and retention expiry.
- Mobile, Voice and SMS advisory paths validate image references against controlled farmer-owned media before allowing them into the advisory context.
- Privacy API for retention disclosure, farmer data export and farmer data deletion; deleting a farmer account invalidates existing bearer tokens because token verification now checks current account state.
- Configurable retention policies for traces/recommendations, history, SMS, images and audit events; manual admin cleanup plus daily production retention worker.
- PostgreSQL UnitOfWork: final trace, recommendation, passport update and history write share one transaction and roll back together on failure.
- Persistence ownership columns for new traces, recommendations and SMS deliveries to support reliable export/deletion.
- Alembic revision `9b81c2276e10` adding controlled-media/audit persistence and ownership columns.
- `/api/v1/ready` now validates database connectivity and expected migration revision in addition to knowledge readiness.
- Daily PostgreSQL custom-format `pg_dump` backup worker, SHA-256 sidecars, configurable backup retention and restore script.
- A safe PostgreSQL integration suite gated by `TEST_DATABASE_URL`, preventing accidental testing against production.

## Verification in this environment

- Python compilation: passed.
- Existing + new automated suite: **85 passed**.
- PostgreSQL-specific integration tests: **2 safely skipped** because this execution environment does not provide a PostgreSQL server or Docker. They are ready to run against an ephemeral database using `TEST_DATABASE_URL`.
- Coverage run after the hardening changes remained above the configured 85% gate.
- Alembic upgrade through the new head revision was executed successfully against a temporary SQL database to validate migration ordering/syntax.

## Still deployment-dependent

The code is prepared, but a real production deployment must still supply a DNS domain, TLS email, strong secrets, production PostgreSQL infrastructure and periodically perform the documented restore drill. Weather, Translation, TTS and real SMS providers remain external adapter integrations to be added when their APIs/credentials are available.
