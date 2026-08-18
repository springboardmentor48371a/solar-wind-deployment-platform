#!/bin/sh
# One-shot backup of both databases into a timestamped directory under
# /backups, then prunes anything older than BACKUP_RETENTION_DAYS.
#
# Run manually:      docker compose exec backup /bin/sh scripts/backup.sh
# Restore Postgres:   gunzip -c /backups/<timestamp>/postgres.sql.gz | \
#                       psql -h db -U swdip_user -d swdip_db
# Restore a Mongo
# collection:         see scripts/restore_mongo.py
#
# Runs as part of the `backup` compose service's loop (backup_loop.sh) on
# BACKUP_INTERVAL_SECONDS, and can also be invoked directly for an
# on-demand backup.
set -eu

BACKUP_ROOT="${BACKUP_ROOT:-/backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
TIMESTAMP="$(date -u +%Y-%m-%dT%H%M%SZ)"
DEST="${BACKUP_ROOT}/${TIMESTAMP}"

mkdir -p "$DEST"
echo "[backup] starting backup -> ${DEST}"

# --- PostgreSQL ---
# PGHOST/PGUSER/PGPASSWORD/PGDATABASE are read automatically by pg_dump
# from the environment (standard libpq behavior) — see docker-compose.yml.
if pg_dump --no-owner --no-privileges | gzip > "${DEST}/postgres.sql.gz"; then
  echo "[backup] postgres: $(du -h "${DEST}/postgres.sql.gz" | cut -f1)"
else
  echo "[backup] WARNING: postgres dump failed — leaving prior backups intact" >&2
  rm -f "${DEST}/postgres.sql.gz"
fi

# --- MongoDB ---
if python scripts/backup_mongo.py "${DEST}/mongo"; then
  echo "[backup] mongo: ok"
else
  echo "[backup] WARNING: mongo dump failed" >&2
fi

# If neither database backup produced any file, remove the empty
# directory rather than accumulating junk timestamps.
if [ -z "$(ls -A "$DEST" 2>/dev/null)" ]; then
  rmdir "$DEST" 2>/dev/null || true
  echo "[backup] nothing was written — both databases were unreachable"
  exit 0
fi

# --- Retention: prune backup directories older than RETENTION_DAYS ---
find "$BACKUP_ROOT" -maxdepth 1 -mindepth 1 -type d -mtime "+${RETENTION_DAYS}" -print | while read -r old_dir; do
  echo "[backup] pruning old backup: ${old_dir}"
  rm -rf "$old_dir"
done

echo "[backup] done"
