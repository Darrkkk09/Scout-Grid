"""
ScoutGrid Phase 5 — Candidate Embeddings Bulk Indexing Script

Reads candidate profiles from MongoDB, converts them into searchable semantic text,
generates vector embeddings via EmbeddingService, and bulk-indexes into OpenSearch.

Usage:
    python scripts/index_candidate_embeddings.py --limit 1000
    python scripts/index_candidate_embeddings.py --limit 31002 --batch-size 1000
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

from app.services.embedding_service import EmbeddingService, candidate_to_semantic_text
from app.services.opensearch_client import create_opensearch_client
from app.services.opensearch_index import (
    CANDIDATES_INDEX_NAME,
    candidate_to_search_document,
    create_candidate_index,
)

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "scoutgrid")


def bulk_index_candidate_embeddings(
    limit: int = 100000,
    batch_size: int = 1000,
    index_name: str = "scoutgrid_candidates_100k",
    resume: bool = True,
    reset_index: bool = False,
) -> Tuple[int, int, int, int, float, float, int]:
    t0 = time.perf_counter()

    print(f"Connecting to MongoDB database '{MONGODB_DATABASE}' at {MONGODB_URI}...")
    mongo_client = MongoClient(MONGODB_URI)
    db = mongo_client[MONGODB_DATABASE]
    collection = db["candidates"]

    total_candidates_in_db = int(collection.count_documents({}))
    target_limit = min(limit, total_candidates_in_db) if limit > 0 else total_candidates_in_db

    print("Connecting to OpenSearch...")
    os_client = create_opensearch_client()

    if reset_index and os_client.indices.exists(index=index_name):
        print(f"Resetting target OpenSearch index '{index_name}'...")
        os_client.indices.delete(index=index_name)
        print(f"Deleted OpenSearch index '{index_name}'.")

    create_candidate_index(os_client, index_name)

    embedding_service = EmbeddingService()

    print("=" * 60)
    print("SCOUTGRID 100K OPENSEARCH INDEXING")
    print("=" * 60)
    print(f"MongoDB candidates: {total_candidates_in_db:,}")
    print(f"OpenSearch index:   {index_name}")
    print(f"Batch size:         {batch_size:,}")
    print(f"Resumable indexing: {resume}")
    print(f"Embedding provider: {embedding_service.provider}")
    print(f"Embedding model:    {embedding_service.model}")
    print(f"Embedding dimension:{embedding_service.dimension}")
    print("\nProgress:\n")

    already_indexed_ids = set()
    if resume and os_client.indices.exists(index=index_name):
        # Scan existing document IDs to allow resumption without re-indexing
        print("  Checking existing document IDs for resumable indexing...")
        try:
            res = helpers.scan(
                os_client,
                index=index_name,
                query={"_source": False, "query": {"match_all": {}}},
                scroll="5m",
            )
            for hit in res:
                already_indexed_ids.add(hit["_id"])
            print(f"  Found {len(already_indexed_ids):,} candidates already in '{index_name}'.")
        except Exception as e:
            print(f"  Warning during resume check: {str(e)}")

    total_read = 0
    embeddings_generated = 0
    total_success = 0
    total_failed = 0

    cursor = collection.find().limit(target_limit)

    batch_docs = []
    for doc in cursor:
        total_read += 1
        cand_id = str(doc.get("_id", doc.get("id")))

        if resume and cand_id in already_indexed_ids:
            continue

        batch_docs.append(doc)

        if len(batch_docs) >= batch_size:
            success, failed, gen_count = _process_and_bulk_index_batch(
                os_client, batch_docs, embedding_service, index_name
            )
            total_success += success
            total_failed += failed
            embeddings_generated += gen_count
            
            current_os_count = len(already_indexed_ids) + total_success
            print(f"  {current_os_count:,} / {target_limit:,} candidates processed")
            batch_docs = []

    # Final batch flush
    if batch_docs:
        success, failed, gen_count = _process_and_bulk_index_batch(
            os_client, batch_docs, embedding_service, index_name
        )
        total_success += success
        total_failed += failed
        embeddings_generated += gen_count

    t1 = time.perf_counter()
    total_time = t1 - t0
    docs_per_sec = total_success / total_time if total_time > 0 else 0.0

    final_os_count = os_client.count(index=index_name).get("count", 0)

    print("\n" + "=" * 60)
    print("INDEXING SUMMARY")
    print("=" * 60)
    print(f"MongoDB candidates:      {total_candidates_in_db:,}")
    print(f"Indexed successfully:    {total_success:,}")
    print(f"Failed:                  {total_failed:,}")
    print(f"Execution time:          {total_time:.2f} seconds")
    print(f"Throughput:              {docs_per_sec:.2f} candidates/sec")
    print(f"OpenSearch total count:  {final_os_count:,}")
    print("=" * 60 + "\n")

    mongo_client.close()
    return total_read, embeddings_generated, total_success, total_failed, total_time, docs_per_sec, final_os_count


def _process_and_bulk_index_batch(
    os_client, batch_docs: list, embedding_service: EmbeddingService, index_name: str
) -> Tuple[int, int, int]:
    actions = []
    embeddings_generated = 0

    semantic_texts = [candidate_to_semantic_text(doc) for doc in batch_docs]
    vectors = embedding_service.embed_texts(semantic_texts)

    for doc, vec in zip(batch_docs, vectors):
        try:
            transformed = candidate_to_search_document(doc)
            transformed["embedding"] = vec
            candidate_id = transformed["candidate_id"]

            actions.append(
                {
                    "_index": index_name,
                    "_id": candidate_id,
                    "_source": transformed,
                }
            )
            embeddings_generated += 1
        except Exception as e:
            print(f"Warning: Failed to transform/embed doc: {str(e)}")

    if not actions:
        return 0, len(batch_docs), 0

    success_count, failed_items = helpers.bulk(
        os_client,
        actions,
        stats_only=False,
        raise_on_error=False,
    )
    failed_count = len(failed_items) if isinstance(failed_items, list) else 0

    return success_count, failed_count, embeddings_generated


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate candidate embeddings and bulk index into OpenSearch safely"
    )
    parser.add_argument(
        "--index",
        type=str,
        default=os.getenv("OPENSEARCH_INDEX_NAME", "scoutgrid_candidates_100k"),
        help="Target OpenSearch index name (default: scoutgrid_candidates_100k)",
    )
    parser.add_argument(
        "--limit", type=int, default=100000, help="Maximum number of candidates to process"
    )
    parser.add_argument(
        "--batch-size", type=int, default=1000, help="Batch size for embeddings & OpenSearch bulk API"
    )
    parser.add_argument(
        "--resume", action="store_true", default=True, help="Enable resumable indexing (skip already indexed IDs)"
    )
    parser.add_argument(
        "--reset-index", action="store_true", help="Delete and recreate target index before indexing"
    )
    args = parser.parse_args()

    bulk_index_candidate_embeddings(
        limit=args.limit,
        batch_size=args.batch_size,
        index_name=args.index,
        resume=args.resume,
        reset_index=args.reset_index,
    )


if __name__ == "__main__":
    main()
