"""
ScoutGrid — Benchmark requirement extraction latency (Rule-based vs Hybrid fallback)

Usage:
    python scripts/benchmark_requirement_extraction.py
"""

import os
import sys
import time
from typing import List

# Ensure backend directory is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from services.hybrid_requirement_extractor import HybridRequirementExtractor
from services.requirement_extractor import RequirementExtractor

TEST_QUERIES = [
    "Python developers",
    "Python backend engineers with 3+ years of experience in Bangalore",
    "React developers with 2+ years of experience in Hyderabad",
    "Software engineers who built scalable microservices and distributed queue systems",
    "Senior Data Engineer with 5+ years experience in Mumbai knowing Kafka and PySpark",
    "Fullstack developer with TypeScript and Node.js",
    "Rust developers with 10+ years in Delhi",
]


def run_extraction_benchmark(iterations: int = 100):
    print("=" * 80)
    print("SCOUTGRID REQUIREMENT EXTRACTION BENCHMARK")
    print(f"Iterations: {iterations} per query")
    print("=" * 80)

    hybrid = HybridRequirementExtractor()

    print(f"{'Query String':<60} | {'Rule Extractor (ms)':<20} | {'Hybrid Mode':<12}")
    print("-" * 100)

    for q in TEST_QUERIES:
        # Rule Extractor Timing
        t0 = time.perf_counter()
        for _ in range(iterations):
            RequirementExtractor.extract(q)
        t1 = time.perf_counter()
        rule_ms = round(((t1 - t0) * 1000.0) / iterations, 4)

        # Hybrid Orchestrator Timing
        t0 = time.perf_counter()
        for _ in range(iterations):
            hybrid.extract(q)
        t1 = time.perf_counter()
        hybrid_ms = round(((t1 - t0) * 1000.0) / iterations, 4)

        _, source, reason = hybrid.extract_with_metadata(q)

        display_q = q[:57] + "..." if len(q) > 60 else q
        print(f"{display_q:<60} | {rule_ms:<20.4f} | {source} ({reason})")

    print("=" * 100)


if __name__ == "__main__":
    run_extraction_benchmark()
