#!/usr/bin/env bash
set -euo pipefail

BACKUP_FILE=${1:-backup.sql}

if [ ! -f "$BACKUP_FILE" ]; then
  echo "Backup file not found: $BACKUP_FILE" >&2
  exit 1
fi

if [ ! -s "$BACKUP_FILE" ]; then
  echo "Backup file is empty." >&2
  exit 1
fi

TMP_DB="prs_verify_$(date +%s)"

printf "Creating temporary DB %s...\n" "$TMP_DB"
docker compose exec -T db createdb -U prs "$TMP_DB"

printf "Restoring into %s...\n" "$TMP_DB"
docker compose exec -T db psql -U prs "$TMP_DB" < "$BACKUP_FILE"

printf "Verifying tables...\n"
docker compose exec -T db psql -U prs "$TMP_DB" -c "\dt" >/dev/null

printf "Dropping temporary DB %s...\n" "$TMP_DB"
docker compose exec -T db dropdb -U prs "$TMP_DB"

echo "Backup verification succeeded."
