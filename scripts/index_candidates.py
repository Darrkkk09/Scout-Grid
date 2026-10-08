"""
ScoutGrid Phase 4 Step 4 — Candidate Bulk Indexing Script

Reads candidate profiles from MongoDB, transforms them into OpenSearch search documents
using candidate_to_search_document(), and indexes them via OpenSearch helpers bulk API in batches.

Usage:
    python scripts/index_candidates.py --limit 1000
    python scripts/index_candidates.py --limit 10000
"""

import argparse
import os
import sys
import time
from typing import Tuple

# Ensure backend directory is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
from opensearchpy import helpers
from pymongo import MongoClient

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

from services.opensearch_client import create_opensearch_client
from services.opensearch_index import (
    CANDIDATES_INDEX_NAME,
    candidate_to_search_document,
    create_candidate_index,
)

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "scoutgrid")


def bulk_index_candidates(limit: int = 10000, batch_size: int = 1000) -> Tuple[int, int, int, float, float]:
    t0 = time.perf_counter()

    print(f"Connecting to MongoDB database '{MONGODB_DATABASE}' at {MONGODB_URI}...")
    mongo_client = MongoClient(MONGODB_URI)
    db = mongo_client[MONGODB_DATABASE]
    collection = db["candidates"]

    try:
        total_candidates_in_db = int(collection.count_documents({}))
    except (TypeError, ValueError):
        total_candidates_in_db = limit

    target_limit = min(limit, total_candidates_in_db) if limit > 0 else total_candidates_in_db

    print(f"Total candidates in MongoDB: {total_candidates_in_db:,}. Targeting index batch limit: {target_limit:,}.")

    print("Connecting to OpenSearch...")
    os_client = create_opensearch_client()

    # Ensure index exists
    create_candidate_index(os_client, CANDIDATES_INDEX_NAME)

    total_read = 0
    total_success = 0
    total_failed = 0

    # Fetch MongoDB candidates in batches
    cursor = collection.find().limit(target_limit)

    batch_actions = []
    for doc in cursor:
        transformed = candidate_to_search_document(doc)
        candidate_id = transformed["candidate_id"]
        batch_actions.append({
            "_index": CANDIDATES_INDEX_NAME,
            "_id": candidate_id,
            "_source": transformed,
        })
        total_read += 1

        if len(batch_actions) >= batch_size:
            success, failed_items = helpers.bulk(
                os_client,
                batch_actions,
                stats_only=False,
                raise_on_error=False,
            )
            failed_count = len(failed_items) if isinstance(failed_items, list) else 0
            total_success += success
            total_failed += failed_count
            print(f"  Indexed batch: {total_success:,} / {target_limit:,} ({total_success/target_limit*100:.1f}%)")
            batch_actions = []

    # Final batch flush
    if batch_actions:
        success, failed_items = helpers.bulk(
            os_client,
            batch_actions,
            stats_only=False,
            raise_on_error=False,
        )
        failed_count = len(failed_items) if isinstance(failed_items, list) else 0
        total_success += success
        total_failed += failed_count

    t1 = time.perf_counter()
    total_time = t1 - t0
    docs_per_sec = total_success / total_time if total_time > 0 else 0.0

    mongo_client.close()
    return total_read, total_success, total_failed, total_time, docs_per_sec


def main() -> None:
    parser = argparse.ArgumentParser(description="Bulk index MongoDB candidates into OpenSearch")
    parser.add_argument("--limit", type=int, default=10000, help="Maximum number of candidates to index")
    parser.add_argument("--batch-size", type=int, default=1000, help="Batch size for OpenSearch bulk API")
    args = parser.parse_args()

    read, success, failed, total_time, throughput = bulk_index_candidates(
        limit=args.limit,
        batch_size=args.batch_size
    )

    print("\n=======================================================")
    print("Bulk Indexing Results:")
    print(f"  Candidates read from MongoDB: {read:,}")
    print(f"  Successfully indexed:         {success:,}")
    print(f"  Failed:                       {failed:,}")
    print(f"  Total indexing time:          {total_time:.2f} seconds")
    print(f"  Indexing throughput:          {throughput:.2f} docs/sec")
    print("=======================================================")


if __name__ == "__main__":
    main()
