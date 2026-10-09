#!/bin/sh
set -eu

: "${POSTGRES_DB:?POSTGRES_DB is required}"
: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}"
POSTGRES_HOST="${POSTGRES_HOST:-database}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
BACKUP_DIR="${BACKUP_DIR:-/backups}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"

mkdir -p "$BACKUP_DIR"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
file="$BACKUP_DIR/${POSTGRES_DB}_${timestamp}.dump"

export PGPASSWORD="$POSTGRES_PASSWORD"
pg_dump \
  --host "$POSTGRES_HOST" \
  --port "$POSTGRES_PORT" \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" \
  --format=custom \
  --no-owner \
  --file "$file"

sha256sum "$file" > "$file.sha256"
find "$BACKUP_DIR" -type f \( -name '*.dump' -o -name '*.dump.sha256' \) \
  -mtime "+$BACKUP_RETENTION_DAYS" -delete
printf 'Backup created: %s\n' "$file"
