# Restoring from a backup

Backups are written by `scripts/backup.sh` (run on a schedule by the
`backup` compose service) into `/backups/<UTC timestamp>/` inside the
`swdip_backups` Docker volume:

```
/backups/2026-08-17T030000Z/
  postgres.sql.gz
  mongo/
    users.json.gz
    projects.json.gz
    weather_raw.json.gz
    ...
```

List available backups:

```
docker compose exec backup ls -la /backups
```

## Restore PostgreSQL

```
docker compose exec -T backup sh -c \
  'gunzip -c /backups/2026-08-17T030000Z/postgres.sql.gz | psql -h db -U swdip_user -d swdip_db'
```

This restores into the *existing* `swdip_db` database. To restore into a
clean database instead (recommended if you're not sure what's already in
there), drop and recreate it first:

```
docker compose exec db psql -U swdip_user -d postgres -c "DROP DATABASE swdip_db;"
docker compose exec db psql -U swdip_user -d postgres -c "CREATE DATABASE swdip_db;"
docker compose exec db psql -U swdip_user -d swdip_db -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

then run the restore command above.

## Restore MongoDB

There's no single `mongorestore` step here since backups are plain JSON
per collection (see `scripts/backup_mongo.py` for why). Restore a
collection with `scripts/restore_mongo.py`:

```
docker compose exec backup python scripts/restore_mongo.py \
  /backups/2026-08-17T030000Z/mongo/weather_raw.json.gz weather_raw
```

This is idempotent-ish but not a merge: it replaces the target
collection's contents entirely with what's in the backup file.

## Restic / off-host copies

The `swdip_backups` volume only protects you against database corruption
or a bad migration — it's still on the same host as everything else. For
real disaster recovery, periodically copy the volume off-host, e.g.:

```
docker run --rm -v swdip_backups:/backups -v "$PWD":/dest alpine \
  tar czf /dest/swdip-backups-$(date +%F).tar.gz -C / backups
```
