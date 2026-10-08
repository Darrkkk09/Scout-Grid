"""
ScoutGrid Phase 5 — Search Quality Evaluation Suite (Precision@10, Recall@10, Hit@10)

Evaluates retrieval quality across BM25, Vector, and Hybrid RRF search modes
using a labeled candidate evaluation set.

Usage:
    python scripts/evaluate_search_quality.py
"""

import asyncio
import os
import sys
from typing import Dict, List, Set

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from database import connect_to_mongo, close_mongo_connection, get_candidates_collection
from services.opensearch_client import get_opensearch_client
from services.opensearch_search_service import OpenSearchService

# Labeled Search Quality Test Suite
EVALUATION_QUERIES = [
    {
        "query": "Python developers in Bangalore",
        "relevant_skills": ["Python"],
        "relevant_location": "Bangalore",
    },
    {
        "query": "React developers in Hyderabad",
        "relevant_skills": ["React"],
        "relevant_location": "Hyderabad",
    },
    {
        "query": "Java Spring Boot engineers with 5+ years",
        "relevant_skills": ["Java", "Spring Boot"],
        "min_exp": 5.0,
    },
    {
        "query": "Backend engineers experienced with distributed systems and microservices",
        "relevant_skills": ["Microservices", "Python", "Go", "Java"],
        "semantic_keywords": ["distributed", "microservices", "api"],
    },
    {
        "query": "Data Engineer knowing Kafka and PostgreSQL",
        "relevant_skills": ["Kafka", "PostgreSQL"],
    },
]


def is_candidate_relevant(cand_doc: dict, eval_item: dict) -> bool:
    """Evaluates whether a returned candidate matches the query relevance rules."""
    skills = set(cand_doc.get("skills", []))
    loc = cand_doc.get("location", "")
    exp_years = cand_doc.get("experience_years", 0.0)

    # Check skill match
    if "relevant_skills" in eval_item:
        rel_skills = set(eval_item["relevant_skills"])
        if not rel_skills.intersection(skills):
            return False

    # Check location match
    if "relevant_location" in eval_item:
        if loc.lower() != eval_item["relevant_location"].lower():
            return False

    # Check min experience match
    if "min_exp" in eval_item:
        if exp_years < eval_item["min_exp"]:
            return False

    return True


async def run_quality_evaluation():
    print("=" * 90)
    print("SCOUTGRID SEARCH QUALITY EVALUATION (Precision@10, Recall@10, Hit@10)")
    print("=" * 90)

    await connect_to_mongo()
    mongo_coll = get_candidates_collection()

    client = get_opensearch_client()
    service = OpenSearchService(client)

    modes = ["bm25", "vector", "hybrid"]
    metrics_summary: Dict[str, Dict[str, float]] = {
        mode: {"precision@10": 0.0, "hit@10": 0.0} for mode in modes
    }

    try:
        for item in EVALUATION_QUERIES:
            q_str = item["query"]
            print(f"\nEvaluating Query: '{q_str}'")

            for mode in modes:
                res = await service.search(query=q_str, page=1, limit=10, search_mode=mode)
                retrieved_candidates = res.results

                relevant_count = 0
                for cand in retrieved_candidates:
                    cand_dict = cand.model_dump()
                    if is_candidate_relevant(cand_dict, item):
                        relevant_count += 1

                precision = relevant_count / len(retrieved_candidates) if retrieved_candidates else 0.0
                hit = 1.0 if relevant_count > 0 else 0.0

                metrics_summary[mode]["precision@10"] += precision
                metrics_summary[mode]["hit@10"] += hit

                print(f"  [{mode.upper():<6}] Precision@10: {precision:.2f} ({relevant_count}/{len(retrieved_candidates)} relevant) | Hit@10: {hit}")

    finally:
        await close_mongo_connection()

    num_queries = len(EVALUATION_QUERIES)

    print("\n" + "=" * 90)
    print(f"{'Search Mode':<12} | {'Mean Precision@10':<20} | {'Mean Hit@10':<15}")
    print("-" * 90)
    for mode in modes:
        mean_prec = metrics_summary[mode]["precision@10"] / num_queries
        mean_hit = metrics_summary[mode]["hit@10"] / num_queries
        print(f"{mode.upper():<12} | {mean_prec:<20.4f} | {mean_hit:<15.4f}")
    print("=" * 90)


if __name__ == "__main__":
    asyncio.run(run_quality_evaluation())
