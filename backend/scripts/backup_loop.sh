#!/bin/sh
# Entry point for the `backup` compose service. Runs backup.sh once
# immediately (so a fresh `docker compose up` gets a backup right away
# instead of waiting a full day), then repeats every
# BACKUP_INTERVAL_SECONDS (default 86400 = daily) for as long as the
# container runs. Deliberately not cron — cron needs a second process/PID
# 1 setup inside the container to behave correctly, and this three-line
# loop needs none of that.
set -eu

cd /app

INTERVAL="${BACKUP_INTERVAL_SECONDS:-86400}"

while true; do
  sh scripts/backup.sh || echo "[backup_loop] backup.sh exited non-zero; will retry next interval" >&2
  echo "[backup_loop] sleeping ${INTERVAL}s until next backup"
  sleep "$INTERVAL"
done
