#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "usage: $0 /backups/<file>.dump" >&2
  exit 2
fi

: "${POSTGRES_DB:?POSTGRES_DB is required}"
: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}"
POSTGRES_HOST="${POSTGRES_HOST:-database}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
file="$1"

[ -f "$file" ] || { echo "backup not found: $file" >&2; exit 2; }
if [ -f "$file.sha256" ]; then
  (cd "$(dirname "$file")" && sha256sum -c "$(basename "$file").sha256")
fi

export PGPASSWORD="$POSTGRES_PASSWORD"
pg_restore \
  --host "$POSTGRES_HOST" \
  --port "$POSTGRES_PORT" \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" \
  --clean \
  --if-exists \
  --no-owner \
  "$file"
printf 'Restore completed from: %s\n' "$file"
