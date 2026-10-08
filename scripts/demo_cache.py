import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from services.opensearch_client import get_opensearch_client
from services.opensearch_search_service import OpenSearchService

async def main():
    service = OpenSearchService(get_opensearch_client())
    query = "Python Backend Engineer in Bangalore"

    print(f"Executing search query: '{query}'...")
    
    # Request 1 (Cache MISS)
    t0 = time.perf_counter()
    res1 = await service.search(query=query, limit=10, search_mode="hybrid")
    t1 = time.perf_counter()
    ms1 = round((t1 - t0) * 1000, 1)

    print(f"Request 1 (CACHE MISS) -> Latency: {ms1} ms | Results returned: {len(res1.results)}")

    # Request 2 (Cache HIT)
    t2 = time.perf_counter()
    res2 = await service.search(query=query, limit=10, search_mode="hybrid")
    t3 = time.perf_counter()
    ms2 = round((t3 - t2) * 1000, 1)

    print(f"Request 2 (CACHE HIT)  -> Latency: {ms2} ms | Results returned: {len(res2.results)}")
    print(f"Speedup Factor: {round(ms1 / ms2, 1)}x faster!")

if __name__ == "__main__":
    asyncio.run(main())
