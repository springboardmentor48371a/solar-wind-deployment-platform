"""
Dumps every collection in the platform's MongoDB (secondary) database to
gzipped JSON files — one file per collection — under a given directory.

Written in pure pymongo rather than shelling out to `mongodump` because
the official Mongo database tools aren't in Debian's default apt repos
(adding MongoDB's own apt repo just for a backup script is more moving
parts than this needs), and pymongo is already a hard dependency of the
app. bson.json_util handles Mongo-specific types (ObjectId, datetime)
that plain `json` can't serialize.

Usage: python scripts/backup_mongo.py /backups/2026-08-17T0300
"""

import gzip
import json
import sys
from pathlib import Path

from bson import json_util
from pymongo import MongoClient

from app.config import settings


def dump_all_collections(output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    client = MongoClient(settings.mongodb_url, serverSelectionTimeoutMS=8000)
    db = client[settings.mongodb_db_name]

    collection_count = 0
    for collection_name in db.list_collection_names():
        out_path = output_dir / f"{collection_name}.json.gz"
        with gzip.open(out_path, "wt", encoding="utf-8") as f:
            documents = list(db[collection_name].find({}))
            f.write(json_util.dumps(documents))
        collection_count += 1
        print(f"  mongo: {collection_name} -> {out_path.name} ({len(documents)} docs)")

    return collection_count


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python backup_mongo.py <output_dir>", file=sys.stderr)
        sys.exit(1)

    try:
        count = dump_all_collections(Path(sys.argv[1]))
        print(f"Mongo backup complete: {count} collection(s).")
    except Exception as exc:  # noqa: BLE001
        # Non-fatal by design: backup.sh continues to prune/report even if
        # one of the two databases was briefly unreachable, and retries
        # again at the next scheduled interval.
        print(f"Warning: Mongo backup failed: {exc}", file=sys.stderr)
        sys.exit(0)
