#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"

if [[ -e .env ]]; then
  printf '%s\n' 'Refusing to overwrite the existing .env. Back it up or configure it manually.' >&2
  exit 1
fi

for command_name in docker openssl; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    printf 'Required command not found: %s\n' "$command_name" >&2
    exit 1
  fi
done

umask 077
database_password="$(openssl rand -hex 32)"
auth_secret="$(openssl rand -hex 32)"
admin_password="$(openssl rand -hex 24)"
cat > .env <<EOF
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
APP_LOG_LEVEL=INFO
KNOWLEDGE_PATH=BASE_CONNAISSANCES_AGRICOLES
SMS_MAX_LENGTH=160
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
POSTGRES_DB=agriadviser
POSTGRES_USER=agriadviser
POSTGRES_PASSWORD=${database_password}
DATABASE_URL=postgresql+psycopg://agriadviser:${database_password}@localhost:5432/agriadviser
AUTH_STORE_PATH=runtime/users-persistent-db.json
AUTH_REQUIRED=false
AUTH_SECRET=${auth_secret}
MEDIA_STORAGE_PATH=runtime/media
ADMIN_USERNAME=admin
ADMIN_PASSWORD=${admin_password}
EOF
unset database_password auth_secret admin_password

printf '%s\n' 'Starting the local API and persistent PostgreSQL database.'
printf '%s\n' 'Database files are stored in the named Docker postgres_data volume.'
exec bash scripts/run_local_backend.sh