"""
ScoutGrid Safe OpenSearch Index Migration / Reindex Workflow Script

Supports safe versioned reindexing (e.g., candidates_v1 -> candidates_v2)
without dropping or deleting existing indices or candidate documents.

Usage:
    python scripts/reindex_opensearch.py --source candidates --target candidates_v2
"""

import argparse
import os
import sys
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
from opensearchpy import helpers

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

from services.opensearch_client import create_opensearch_client
from services.opensearch_index import (
    CANDIDATE_INDEX_MAPPING,
    check_index_exists,
    create_candidate_index,
)


def safe_reindex(source_index: str, target_index: str):
    print(f"Connecting to OpenSearch to reindex from '{source_index}' to '{target_index}'...")
    client = create_opensearch_client()

    if not check_index_exists(client, source_index):
        print(f"Error: Source index '{source_index}' does not exist.")
        return

    # Ensure target index exists
    create_candidate_index(client, target_index)

    print(f"Starting OpenSearch reindex API execution from '{source_index}' to '{target_index}'...")
    t0 = time.perf_counter()

    reindex_body = {
        "source": {"index": source_index},
        "dest": {"index": target_index},
    }

    response = client.reindex(body=reindex_body)
    t1 = time.perf_counter()

    created_count = response.get("created", 0)
    updated_count = response.get("updated", 0)
    failures = response.get("failures", [])

    print("\n=======================================================")
    print("Reindex Execution Results:")
    print(f"  Source index:       {source_index}")
    print(f"  Target index:       {target_index}")
    print(f"  Documents created:  {created_count:,}")
    print(f"  Documents updated:  {updated_count:,}")
    print(f"  Failures:           {len(failures):,}")
    print(f"  Elapsed time:       {t1 - t0:.2f} seconds")
    print("=======================================================")


def main():
    parser = argparse.ArgumentParser(description="Safe OpenSearch versioned index reindexing script")
    parser.add_argument("--source", type=str, default="candidates", help="Source index name")
    parser.add_argument("--target", type=str, default="candidates_v2", help="Target versioned index name")
    args = parser.parse_args()

    safe_reindex(args.source, args.target)


if __name__ == "__main__":
    main()
