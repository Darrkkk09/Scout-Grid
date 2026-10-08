"""
ScoutGrid Phase 5 — Hybrid Search Benchmark Suite (BM25 vs Vector vs Hybrid RRF)

Usage:
    python scripts/benchmark_hybrid_search.py --warmup 5 --iterations 20
"""

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from services.opensearch_client import get_opensearch_client
from services.opensearch_search_service import OpenSearchService
from scripts.benchmark_search import BENCHMARK_QUERIES, calculate_percentiles


async def run_hybrid_benchmark(warmup: int, iterations: int):
    print("=" * 110)
    print("SCOUTGRID BENCHMARK: OpenSearch BM25 vs Vector vs Hybrid RRF Search")
    print(f"Configurations: Warmup = {warmup} | Iterations = {iterations} | Page Limit = 20")
    print("=" * 110)

    t_start = datetime.now()
    client = get_opensearch_client()
    service = OpenSearchService(client)

    results = []

    for q_item in BENCHMARK_QUERIES:
        q_str = q_item["query"]
        q_id = q_item["id"]
        cat = q_item["category"]

        # 1. BM25 Mode
        for _ in range(warmup):
            await service.search(query=q_str, page=1, limit=20, search_mode="bm25")

        bm25_times = []
        bm25_res = None
        for _ in range(iterations):
            t0 = time.perf_counter()
            bm25_res = await service.search(query=q_str, page=1, limit=20, search_mode="bm25")
            t1 = time.perf_counter()
            bm25_times.append((t1 - t0) * 1000.0)

        bm25_stats = calculate_percentiles(bm25_times)
        bm25_ids = set(c.id for c in bm25_res.results)

        # 2. Vector Mode
        for _ in range(warmup):
            await service.search(query=q_str, page=1, limit=20, search_mode="vector")

        vec_times = []
        vec_res = None
        for _ in range(iterations):
            t0 = time.perf_counter()
            vec_res = await service.search(query=q_str, page=1, limit=20, search_mode="vector")
            t1 = time.perf_counter()
            vec_times.append((t1 - t0) * 1000.0)

        vec_stats = calculate_percentiles(vec_times)
        vec_ids = set(c.id for c in vec_res.results)

        # 3. Hybrid Mode
        for _ in range(warmup):
            await service.search(query=q_str, page=1, limit=20, search_mode="hybrid")

        hyb_times = []
        hyb_res = None
        for _ in range(iterations):
            t0 = time.perf_counter()
            hyb_res = await service.search(query=q_str, page=1, limit=20, search_mode="hybrid")
            t1 = time.perf_counter()
            hyb_times.append((t1 - t0) * 1000.0)

        hyb_stats = calculate_percentiles(hyb_times)
        hyb_ids = set(c.id for c in hyb_res.results)

        # Calculate result set overlaps
        bm25_vec_overlap = len(bm25_ids.intersection(vec_ids))
        bm25_hyb_overlap = len(bm25_ids.intersection(hyb_ids))
        vec_hyb_overlap = len(vec_ids.intersection(hyb_ids))

        results.append({
            "id": q_id,
            "category": cat,
            "query": q_str,
            "bm25_stats": bm25_stats,
            "vector_stats": vec_stats,
            "hybrid_stats": hyb_stats,
            "overlaps": {
                "bm25_intersect_vector": bm25_vec_overlap,
                "bm25_intersect_hybrid": bm25_hyb_overlap,
                "vector_intersect_hybrid": vec_hyb_overlap,
            }
        })

    t_end = datetime.now()

    # Print Summary Table
    print("\n" + "=" * 110)
    print(f"{'ID':<4} | {'Category':<26} | {'BM25 p50 / p95 (ms)':<20} | {'Vector p50 / p95 (ms)':<22} | {'Hybrid RRF p50 / p95 (ms)'}")
    print("-" * 110)
    for r in results:
        b = r["bm25_stats"]
        v = r["vector_stats"]
        h = r["hybrid_stats"]
        print(
            f"{r['id']:<4} | {r['category']:<26} | "
            f"{b['p50']:<6.2f} / {b['p95']:<8.2f} | "
            f"{v['p50']:<6.2f} / {v['p95']:<10.2f} | "
            f"{h['p50']:<6.2f} / {h['p95']:<8.2f}"
        )
    print("=" * 110)

    # Save Markdown Report
    md_path = os.path.join(PROJECT_ROOT, "benchmarks", "reports", "hybrid-search-benchmark.md")
    os.makedirs(os.path.dirname(md_path), exist_ok=True)
    md = []
    md.append("# ScoutGrid — Phase 5: Hybrid Search Benchmark Report\n")
    md.append(f"**Execution Timestamp:** `{t_start.isoformat()}`  ")
    md.append(f"**Warmup Iterations:** `{warmup}` | **Measured Iterations:** `{iterations}`  \n")
    md.append("## 1. Search Latency & Overlap Comparison\n")
    md.append("| Query ID | Category | Query String | BM25 p50 (ms) | BM25 p95 (ms) | Vector p50 (ms) | Vector p95 (ms) | Hybrid p50 (ms) | Hybrid p95 (ms) | BM25 ∩ Vector | BM25 ∩ Hybrid | Vector ∩ Hybrid |")
    md.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in results:
        b = r["bm25_stats"]
        v = r["vector_stats"]
        h = r["hybrid_stats"]
        o = r["overlaps"]
        md.append(
            f"| {r['id']} | {r['category']} | `{r['query']}` | {b['p50']} | {b['p95']} | "
            f"{v['p50']} | {v['p95']} | **{h['p50']}** | **{h['p95']}** | "
            f"{o['bm25_intersect_vector']} | {o['bm25_intersect_hybrid']} | {o['vector_intersect_hybrid']} |"
        )
    md.append("\n")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"\nSaved benchmark report to '{md_path}'.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--iterations", type=int, default=20)
    args = parser.parse_args()
    asyncio.run(run_hybrid_benchmark(args.warmup, args.iterations))


if __name__ == "__main__":
    main()
