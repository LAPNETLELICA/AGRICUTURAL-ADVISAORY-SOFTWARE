# AgriSense V1 Production Deployment

## 1. Required environment

Copy `.env.example` to a secret deployment environment (do not commit `.env`) and set at minimum:

- `APP_ENV=production`
- strong random `AUTH_SECRET`
- `AUTH_REQUIRED=true`
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `DOMAIN` pointing to the deployment host
- `TLS_EMAIL` for certificate issuance
- production CORS origins

Provider credentials can remain absent while Weather/Translation/TTS/SMS adapters are disabled or simulated according to the V1 product contract.

## 2. HTTPS/TLS

Run:

```sh
docker compose --profile production up -d
```

The production profile starts Caddy in front of FastAPI. Caddy obtains/renews certificates for `DOMAIN`, redirects HTTP to HTTPS, adds HSTS and security headers, and proxies only to the internal API service. PostgreSQL remains bound to loopback and is not publicly exposed.

## 3. Migrations and readiness

The API runs `alembic upgrade head` before Uvicorn. `/api/v1/ready` checks database connectivity, the expected Alembic revision, and production knowledge availability. Traffic should only be routed while readiness is healthy.

## 4. Image evidence

Images are uploaded to `POST /api/v1/media/images` before their returned `image_id` is referenced in advisory evidence. Files are kept outside public static paths and retrieval/deletion requires authentication plus ownership. JPEG, PNG and WebP signatures are checked and file size is limited by `MEDIA_MAX_BYTES`.

V1 treats images only as farmer-provided evidence. Disease classification remains a V2 feature.

## 5. Retention/privacy

The production profile runs a daily retention worker. Operators can also run:

```sh
python scripts/cleanup_retention.py
```

or the admin endpoint `POST /api/v1/admin/retention/run`.

Farmer export/deletion endpoints are under `/api/v1/privacy`.

## 6. PostgreSQL backup/restore

The production profile runs `backup-worker`, creating a PostgreSQL custom-format `pg_dump` every 24 hours and a SHA-256 sidecar in the `database_backups` volume. Retention is controlled by `BACKUP_RETENTION_DAYS`.

A restore drill should be performed regularly against a non-production database using:

```sh
POSTGRES_HOST=<host> POSTGRES_DB=<restore_db> POSTGRES_USER=<user> \
POSTGRES_PASSWORD=<secret> ./scripts/restore_db.sh /backups/<backup>.dump
```

A backup is not considered operationally valid until a restore drill has succeeded.
