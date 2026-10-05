import os
import sys
import time
import math
import statistics
import logging
from typing import Dict, List, Any

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.services.opensearch_client import get_opensearch_client
from app.services.opensearch_search_service import OpenSearchService, reciprocal_rank_fusion
from app.services.requirement_extractor import RequirementExtractor
from app.services.ranking_service import CandidateRankingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("evaluate_ranking")

INDEX_NAME = os.getenv("OPENSEARCH_INDEX_NAME", "scoutgrid_candidates_100k")

# Labeled test queries with target relevant criteria for automated precision/recall/NDCG evaluation
EVAL_BENCHMARK_QUERIES = [
    {
        "query": "Senior Python Backend Engineer in Bangalore with 5 years experience and FastAPI, PostgreSQL",
        "target_skills": ["python", "fastapi", "postgresql"],
        "target_min_exp": 4.0,
        "target_location": "bangalore",
    },
    {
        "query": "React Frontend Developer with TypeScript and 3 years experience",
        "target_skills": ["react", "typescript"],
        "target_min_exp": 2.0,
        "target_location": None,
    },
    {
        "query": "DevOps Engineer with Docker, Kubernetes, AWS in Remote",
        "target_skills": ["docker", "kubernetes", "aws"],
        "target_min_exp": 3.0,
        "target_location": "remote",
    },
    {
        "query": "Machine Learning Engineer with PyTorch, TensorFlow, Python",
        "target_skills": ["python", "pytorch", "tensorflow"],
        "target_min_exp": 2.0,
        "target_location": None,
    },
    {
        "query": "Java Spring Boot Engineer with Kafka, Microservices, MySQL",
        "target_skills": ["java", "spring boot", "kafka"],
        "target_min_exp": 3.0,
        "target_location": None,
    },
    {
        "query": "Go Cloud Developer with Kubernetes and gRPC",
        "target_skills": ["go", "kubernetes", "grpc"],
        "target_min_exp": 2.0,
        "target_location": None,
    },
    {
        "query": "Data Engineer with Spark, Hadoop, Python, SQL in Mumbai",
        "target_skills": ["spark", "python", "sql"],
        "target_min_exp": 3.0,
        "target_location": "mumbai",
    },
    {
        "query": "Full Stack Engineer Node.js React MongoDB GraphQL",
        "target_skills": ["node.js", "react", "mongodb"],
        "target_min_exp": 2.0,
        "target_location": None,
    }
]


def judge_candidate_relevance(cand_dict: Dict[str, Any], query_spec: Dict[str, Any]) -> int:
    """
    Assigns relevance score (0 = irrelevant, 1 = relevant, 2 = highly relevant).
    """
    cand_skills = [s.lower() for s in cand_dict.get("skills", [])]
    target_skills = query_spec.get("target_skills", [])
    
    matched_skills = [s for s in target_skills if any(s in cs for cs in cand_skills)]
    skill_match_ratio = len(matched_skills) / len(target_skills) if target_skills else 1.0

    exp_years = float(cand_dict.get("experience_years", 0.0))
    min_exp = query_spec.get("target_min_exp")
    exp_ok = (min_exp is None) or (exp_years >= min_exp)

    loc = cand_dict.get("location", "").lower()
    target_loc = query_spec.get("target_location")
    loc_ok = (target_loc is None) or (target_loc in loc)

    if skill_match_ratio >= 0.75 and exp_ok and loc_ok:
        return 2  # Highly relevant
    elif skill_match_ratio >= 0.5 and exp_ok:
        return 1  # Relevant
    else:
        return 0  # Irrelevant


def calculate_metrics(relevance_scores: List[int], k: int = 10) -> Dict[str, float]:
    top_k = relevance_scores[:k]
    rel_count = sum(1 for r in top_k if r > 0)

    # Precision@K
    precision = rel_count / k if k > 0 else 0.0

    # Hit@K
    hit = 1.0 if rel_count > 0 else 0.0

    # MRR (Mean Reciprocal Rank)
    mrr = 0.0
    for idx, r in enumerate(top_k, start=1):
        if r > 0:
            mrr = 1.0 / idx
            break

    # DCG@K
    dcg = sum((2**r - 1) / math.log2(idx + 1) for idx, r in enumerate(top_k, start=1))

    # IDCG@K (Ideal DCG)
    ideal_scores = sorted(relevance_scores, reverse=True)[:k]
    idcg = sum((2**r - 1) / math.log2(idx + 1) for idx, r in enumerate(ideal_scores, start=1))
    ndcg = (dcg / idcg) if idcg > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "hit": round(hit, 4),
        "mrr": round(mrr, 4),
        "ndcg": round(ndcg, 4),
    }


def percentile(data: List[float], p: float) -> float:
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_data[int(k)]
    d0 = sorted_data[int(f)] * (c - k)
    d1 = sorted_data[int(c)] * (k - f)
    return d0 + d1


async def run_evaluation_and_benchmark():
    client = get_opensearch_client()
    service = OpenSearchService(client, index_name=INDEX_NAME)
    extractor = RequirementExtractor()
    ranker = CandidateRankingService()

    logger.info("Starting Evaluation and Latency Benchmark on index '%s'...", INDEX_NAME)

    baseline_metrics_list = []
    ranked_metrics_list = []

    retrieval_latencies = []
    ranking_latencies = []
    total_ranked_latencies = []

    for idx, qspec in enumerate(EVAL_BENCHMARK_QUERIES, start=1):
        query_text = qspec["query"]
        requirements = extractor.extract(query_text)

        # 1. Baseline: OpenSearch Retrieval Pool (Retrieve top 200 candidates)
        t_start_ret = time.perf_counter()
        
        # BM25 Batch
        bm25_query = service.build_opensearch_query(requirements)
        res = client.search(index=INDEX_NAME, body={"query": bm25_query, "from": 0, "size": 200, "track_total_hits": True})
        bm25_hits = res.get("hits", {}).get("hits", [])
        
        # Vector Batch
        vector_hits = service.search_vector(query_text, requirements, limit=200)

        # Fusion
        if bm25_hits and vector_hits:
            retrieved_hits = reciprocal_rank_fusion(bm25_hits, vector_hits, rrf_k=60, top_k=200)
        elif bm25_hits:
            retrieved_hits = bm25_hits
        elif vector_hits:
            retrieved_hits = vector_hits
        else:
            retrieved_hits = []

        ret_time_ms = (time.perf_counter() - t_start_ret) * 1000.0
        retrieval_latencies.append(ret_time_ms)

        # Baseline Top 10 evaluation
        base_top10 = retrieved_hits[:10]
        base_cand_dicts = [h.get("_source", {}) for h in base_top10]
        base_relevance = [judge_candidate_relevance(cd, qspec) for cd in base_cand_dicts]
        base_metrics = calculate_metrics(base_relevance, k=10)
        baseline_metrics_list.append(base_metrics)

        # 2. Ranking Layer Execution
        t_start_rnk = time.perf_counter()
        ranked_candidates = ranker.rank_candidates(retrieved_hits, requirements, top_k=10)
        rnk_time_ms = (time.perf_counter() - t_start_rnk) * 1000.0

        total_ms = ret_time_ms + rnk_time_ms
        ranking_latencies.append(rnk_time_ms)
        total_ranked_latencies.append(total_ms)

        ranked_cand_dicts = [rc.candidate.model_dump() for rc in ranked_candidates]
        ranked_relevance = [judge_candidate_relevance(cd, qspec) for cd in ranked_cand_dicts]
        ranked_metrics = calculate_metrics(ranked_relevance, k=10)
        ranked_metrics_list.append(ranked_metrics)

        logger.info(
            "Query %d: Base P@10=%.2f, Ranked P@10=%.2f | Base NDCG=%.2f, Ranked NDCG=%.2f | Ret: %.1fms, Rank: %.1fms",
            idx, base_metrics["precision"], ranked_metrics["precision"],
            base_metrics["ndcg"], ranked_metrics["ndcg"], ret_time_ms, rnk_time_ms
        )

    # Compute Averages
    avg_base_p10 = float(statistics.mean([m["precision"] for m in baseline_metrics_list]))
    avg_rank_p10 = float(statistics.mean([m["precision"] for m in ranked_metrics_list]))

    avg_base_mrr = float(statistics.mean([m["mrr"] for m in baseline_metrics_list]))
    avg_rank_mrr = float(statistics.mean([m["mrr"] for m in ranked_metrics_list]))

    avg_base_ndcg = float(statistics.mean([m["ndcg"] for m in baseline_metrics_list]))
    avg_rank_ndcg = float(statistics.mean([m["ndcg"] for m in ranked_metrics_list]))

    # Compute Latency Percentiles
    ret_p50 = percentile(retrieval_latencies, 50)
    ret_p95 = percentile(retrieval_latencies, 95)
    ret_p99 = percentile(retrieval_latencies, 99)

    rnk_p50 = percentile(ranking_latencies, 50)
    rnk_p95 = percentile(ranking_latencies, 95)
    rnk_p99 = percentile(ranking_latencies, 99)

    tot_p50 = percentile(total_ranked_latencies, 50)
    tot_p95 = percentile(total_ranked_latencies, 95)
    tot_p99 = percentile(total_ranked_latencies, 99)

    print("\n" + "=" * 65)
    print("         SCOUTGRID PHASE 6 RANKING EVALUATION REPORT        ")
    print("=" * 65)
    print(f"Target Index: {INDEX_NAME}")
    print(f"Evaluation Queries: {len(EVAL_BENCHMARK_QUERIES)}")
    print("-" * 65)
    print("SEARCH QUALITY METRICS (Top 10):")
    print(f"  Precision@10  | Baseline: {avg_base_p10:.4f}  --> Ranked: {avg_rank_p10:.4f}  (Delta {(avg_rank_p10-avg_base_p10)*100:+.1f}%)")
    print(f"  MRR           | Baseline: {avg_base_mrr:.4f}  --> Ranked: {avg_rank_mrr:.4f}  (Delta {(avg_rank_mrr-avg_base_mrr)*100:+.1f}%)")
    print(f"  NDCG@10       | Baseline: {avg_base_ndcg:.4f}  --> Ranked: {avg_rank_ndcg:.4f}  (Delta {(avg_rank_ndcg-avg_base_ndcg)*100:+.1f}%)")
    print("-" * 65)
    print("LATENCY BREAKDOWN (ms):")
    print(f"  OpenSearch Retrieval (200 pool) : p50 = {ret_p50:.1f}ms | p95 = {ret_p95:.1f}ms | p99 = {ret_p99:.1f}ms")
    print(f"  Candidate Feature Ranking (200 pool) : p50 = {rnk_p50:.1f}ms | p95 = {rnk_p95:.1f}ms | p99 = {rnk_p99:.1f}ms")
    print(f"  Total Search (Retrieval + Rank)      : p50 = {tot_p50:.1f}ms | p95 = {tot_p95:.1f}ms | p99 = {tot_p99:.1f}ms")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_evaluation_and_benchmark())
