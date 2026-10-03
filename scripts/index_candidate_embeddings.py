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
    limit: int = 31002, batch_size: int = 1000
) -> Tuple[int, int, int, int, float, float]:
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

    print(
        f"Total candidates in MongoDB: {total_candidates_in_db:,}. Targeting index batch limit: {target_limit:,}."
    )

    print("Connecting to OpenSearch...")
    os_client = create_opensearch_client()
    create_candidate_index(os_client, CANDIDATES_INDEX_NAME)

    embedding_service = EmbeddingService()
    print(
        f"Embedding Provider: {embedding_service.provider} | Model: {embedding_service.model} | Dimension: {embedding_service.dimension}"
    )

    total_read = 0
    embeddings_generated = 0
    total_success = 0
    total_failed = 0

    cursor = collection.find().limit(target_limit)

    batch_docs = []
    for doc in cursor:
        batch_docs.append(doc)
        total_read += 1

        if len(batch_docs) >= batch_size:
            success, failed, gen_count = _process_and_bulk_index_batch(
                os_client, batch_docs, embedding_service
            )
            total_success += success
            total_failed += failed
            embeddings_generated += gen_count
            print(
                f"  Indexed batch: {total_success:,} / {target_limit:,} ({total_success/target_limit*100:.1f}%)"
            )
            batch_docs = []

    # Final batch flush
    if batch_docs:
        success, failed, gen_count = _process_and_bulk_index_batch(
            os_client, batch_docs, embedding_service
        )
        total_success += success
        total_failed += failed
        embeddings_generated += gen_count

    t1 = time.perf_counter()
    total_time = t1 - t0
    docs_per_sec = total_success / total_time if total_time > 0 else 0.0

    mongo_client.close()
    return total_read, embeddings_generated, total_success, total_failed, total_time, docs_per_sec


def _process_and_bulk_index_batch(
    os_client, batch_docs: list, embedding_service: EmbeddingService
) -> Tuple[int, int, int]:
    actions = []
    embeddings_generated = 0

    # Generate semantic texts for batch
    semantic_texts = [candidate_to_semantic_text(doc) for doc in batch_docs]

    # Generate batch embeddings
    vectors = embedding_service.embed_texts(semantic_texts)

    for doc, vec in zip(batch_docs, vectors):
        try:
            transformed = candidate_to_search_document(doc)
            transformed["embedding"] = vec
            candidate_id = transformed["candidate_id"]

            actions.append(
                {
                    "_index": CANDIDATES_INDEX_NAME,
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
        description="Generate candidate embeddings and bulk index into OpenSearch"
    )
    parser.add_argument(
        "--limit", type=int, default=31002, help="Maximum number of candidates to process"
    )
    parser.add_argument(
        "--batch-size", type=int, default=1000, help="Batch size for embeddings & OpenSearch bulk API"
    )
    args = parser.parse_args()

    read, generated, success, failed, total_time, throughput = bulk_index_candidate_embeddings(
        limit=args.limit, batch_size=args.batch_size
    )

    print("\n=======================================================")
    print("Candidate Embedding & Bulk Indexing Results:")
    print(f"  Candidates read from MongoDB: {read:,}")
    print(f"  Embeddings generated:         {generated:,}")
    print(f"  Successfully indexed:         {success:,}")
    print(f"  Failed:                       {failed:,}")
    print(f"  Total processing time:        {total_time:.2f} seconds")
    print(f"  Throughput:                   {throughput:.2f} candidates/sec")
    print("=======================================================")


if __name__ == "__main__":
    main()
