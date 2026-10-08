import asyncio
import os
import sys
from pymongo import MongoClient

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from database import connect_to_mongo, close_mongo_connection, get_candidates_collection
from services.search_service import SearchService
from services.opensearch_client import get_opensearch_client
from services.opensearch_search_service import OpenSearchService
from scripts.benchmark_search import BENCHMARK_QUERIES

async def validate_overlap():
    await connect_to_mongo()
    m_coll = get_candidates_collection()
    m_svc = SearchService(m_coll)
    os_client = get_opensearch_client()
    os_svc = OpenSearchService(os_client, index_name="scoutgrid_candidates_100k")

    print("=" * 80)
    print("STEP 10 — SEARCH PARITY & OVERLAP VALIDATION (100K DATASET)")
    print("=" * 80)

    for q in BENCHMARK_QUERIES:
        q_str = q["query"]
        q_id = q["id"]
        m_res = await m_svc.search(q_str, page=1, limit=20)
        os_res = await os_svc.search(q_str, page=1, limit=20, search_mode="bm25")

        m_ids = set(c.id for c in m_res.results)
        os_ids = set(c.id for c in os_res.results)

        overlap = len(m_ids.intersection(os_ids))
        missing = m_ids - os_ids
        extra = os_ids - m_ids

        print(f"[{q_id}] Query: '{q_str}'")
        print(f"  MongoDB Matched Total:  {m_res.total:,}")
        print(f"  OpenSearch Matched Total: {os_res.total:,}")
        print(f"  Top-20 Result ID Overlap: {overlap} / 20")
        if missing:
            print(f"  Missing IDs in OpenSearch: {list(missing)[:3]}")
        if extra:
            print(f"  Extra IDs in OpenSearch:   {list(extra)[:3]}")
        print("-" * 80)

if __name__ == "__main__":
    asyncio.run(validate_overlap())
