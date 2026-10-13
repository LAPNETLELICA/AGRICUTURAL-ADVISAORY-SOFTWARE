#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"

if [[ ! -f .env ]]; then
  printf '%s\n' 'Missing .env. Run bash scripts/setup_local_database.sh first.' >&2
  exit 1
fi

for command_name in docker; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    printf 'Required command not found: %s\n' "$command_name" >&2
    exit 1
  fi
done

set -a
# shellcheck disable=SC1091
. ./.env
set +a

docker compose up -d database

if [[ ! -x .venv/bin/alembic || ! -x .venv/bin/uvicorn ]]; then
  printf '%s\n' 'Project venv tools missing. Run: uv sync --extra dev' >&2
  exit 1
fi

DATABASE_URL="$DATABASE_URL" .venv/bin/alembic upgrade head
mkdir -p "$(dirname "${AUTH_STORE_PATH:-runtime/users-persistent-db.json}")"
exec .venv/bin/uvicorn api.app:app --host "${APP_HOST:-127.0.0.1}" --port "${APP_PORT:-8000}"