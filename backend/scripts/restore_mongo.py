"""
Restores a single MongoDB collection from a gzipped JSON file produced by
backup_mongo.py. Replaces the target collection's contents entirely — not
a merge.

Usage: python scripts/restore_mongo.py /backups/<ts>/mongo/weather_raw.json.gz weather_raw
"""

import gzip
import sys

from bson import json_util
from pymongo import MongoClient

from app.config import settings


def restore_collection(file_path: str, collection_name: str) -> int:
    client = MongoClient(settings.mongodb_url, serverSelectionTimeoutMS=8000)
    db = client[settings.mongodb_db_name]

    with gzip.open(file_path, "rt", encoding="utf-8") as f:
        documents = json_util.loads(f.read())

    db[collection_name].delete_many({})
    if documents:
        db[collection_name].insert_many(documents)
    return len(documents)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python restore_mongo.py <backup_file.json.gz> <collection_name>", file=sys.stderr)
        sys.exit(1)

    count = restore_collection(sys.argv[1], sys.argv[2])
    print(f"Restored {count} document(s) into '{sys.argv[2]}'.")
