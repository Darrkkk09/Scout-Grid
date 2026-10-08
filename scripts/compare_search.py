import asyncio
import os
import sys
import time
from typing import Any, Dict, List

# Ensure backend root is on Python path
backend_path = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, os.path.abspath(backend_path))

from database import connect_to_mongo, close_mongo_connection, get_candidates_collection
from services.opensearch_client import get_opensearch_client
from services.search_service import SearchService
from services.opensearch_search_service import OpenSearchService

TEST_QUERIES = [
    "Python developers",
    "Python in Bangalore",
    "Python FastAPI",
    "Python backend 3+ years",
    "Python backend 3+ years Bangalore",
    "React 2+ years",
    "software engineers 4+ years",
    "Rust 10+ years Hyderabad",
]


async def run_comparison():
    print("=" * 70)
    print("SCOUTGRID SEARCH COMPARISON: MongoDB vs OpenSearch")
    print("=" * 70)

    # 1. Connect MongoDB & OpenSearch
    await connect_to_mongo()
    mongo_coll = get_candidates_collection()
    mongo_service = SearchService(mongo_coll)

    opensearch_client = get_opensearch_client()
    opensearch_service = OpenSearchService(opensearch_client)

    all_matched = True

    try:
        for q in TEST_QUERIES:
            # Execute MongoDB search
            mongo_res = await mongo_service.search(query=q, page=1, limit=50)
            mongo_ids = set(c.id for c in mongo_res.results)

            # Execute OpenSearch search
            opensearch_res = await opensearch_service.search(query=q, page=1, limit=50)
            opensearch_ids = set(c.id for c in opensearch_res.results)

            # Note: MongoDB has total collection count, OpenSearch only indexed subset (e.g. 100 candidates)
            print(f"\nQuery: '{q}'")
            print(f"  - MongoDB Total Matches (Full DB): {mongo_res.total} | Returned Top 50: {len(mongo_res.results)}")
            print(f"  - OpenSearch Total Matches (100 Indexed): {opensearch_res.total} | Returned Top 50: {len(opensearch_res.results)}")

            # Check overlap among the candidates that exist in the indexed candidate set
            print(f"  - MongoDB Top Match IDs sample: {list(mongo_ids)[:3]}")
            print(f"  - OpenSearch Top Match IDs sample: {list(opensearch_ids)[:3]}")

    finally:
        await close_mongo_connection()

    print("\n" + "=" * 70)
    print("Comparison Complete.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_comparison())
