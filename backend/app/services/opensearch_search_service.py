import math
import logging
import os
from typing import Any, Dict, List, Optional, Tuple
from opensearchpy import OpenSearch

from app.models.candidate import CandidateResponse
from app.models.search import (
    PaginationMode,
    ParsedRequirements,
    SearchRequest,
    SearchResponse,
)
from app.services.cache_service import CacheService
from app.services.embedding_service import EmbeddingService
from app.services.hybrid_requirement_extractor import HybridRequirementExtractor
from app.services.opensearch_index import CANDIDATES_INDEX_NAME
from app.services.ranking_service import CandidateRankingService
from app.services.requirement_extractor import RequirementExtractor

logger = logging.getLogger(__name__)


def reciprocal_rank_fusion(
    bm25_hits: List[Dict[str, Any]],
    vector_hits: List[Dict[str, Any]],
    rrf_k: int = 60,
    top_k: int = 20,
) -> List[Dict[str, Any]]:
    """
    Combines BM25 hits and Vector hits using Reciprocal Rank Fusion (RRF).
    Formula: score(doc) = 1.0 / (k + rank_bm25) + 1.0 / (k + rank_vector)
    Deduplicates candidates appearing in both result lists and computes combined RRF score.
    """
    scores: Dict[str, float] = {}
    doc_map: Dict[str, Dict[str, Any]] = {}

    for rank, hit in enumerate(bm25_hits, start=1):
        source = hit.get("_source", {})
        cand_id = str(source.get("candidate_id", hit.get("_id")))
        scores[cand_id] = scores.get(cand_id, 0.0) + (1.0 / (rrf_k + rank))
        if cand_id not in doc_map:
            doc_map[cand_id] = hit

    for rank, hit in enumerate(vector_hits, start=1):
        source = hit.get("_source", {})
        cand_id = str(source.get("candidate_id", hit.get("_id")))
        scores[cand_id] = scores.get(cand_id, 0.0) + (1.0 / (rrf_k + rank))
        if cand_id not in doc_map:
            doc_map[cand_id] = hit

    # Sort candidate IDs by descending combined RRF score
    sorted_ids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)

    fused_hits = []
    for cand_id in sorted_ids[:top_k]:
        hit = doc_map[cand_id]
        hit["_rrf_score"] = round(scores[cand_id], 6)
        fused_hits.append(hit)

    return fused_hits


class OpenSearchService:
    """
    Candidate Search Service using OpenSearch.
    Supports BM25 structured filter search, k-NN Vector Search, and Hybrid RRF Search modes.
    """

    def __init__(
        self,
        client: OpenSearch,
        index_name: str = CANDIDATES_INDEX_NAME,
        embedding_service: Optional[EmbeddingService] = None,
        cache_service: Optional[CacheService] = None,
    ):
        self.client = client
        self.index_name = index_name
        self.embedding_service = embedding_service or EmbeddingService()
        self.cache_service = cache_service or CacheService()

        # Hybrid search configuration
        self.rrf_k = int(os.getenv("HYBRID_RRF_K", "60"))
        self.candidate_multiplier = int(os.getenv("HYBRID_CANDIDATE_MULTIPLIER", "5"))

    def build_opensearch_query(
        self,
        requirements: ParsedRequirements,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        filter_clauses: List[Dict[str, Any]] = []
        must_clauses: List[Dict[str, Any]] = []

        # 1. Skills matching (Exact keyword match for ALL skills using term filters)
        combined_skills = list(requirements.skills)
        if filters and filters.get("skill"):
            override_skill = str(filters["skill"]).strip()
            if override_skill and override_skill not in combined_skills:
                combined_skills.append(override_skill)

        for skill in combined_skills:
            filter_clauses.append({"term": {"skills": skill}})

        # 2. Location filter (Exact term match on keyword field)
        location = (filters.get("location") if filters else None) or requirements.location
        if location and str(location).strip():
            loc_str = str(location).strip()
            filter_clauses.append({"term": {"location": loc_str}})

        # 3. Experience years range filter
        min_exp = requirements.min_experience
        max_exp = requirements.max_experience

        if filters and filters.get("min_experience") is not None:
            try:
                override_min = float(filters["min_experience"])
                min_exp = max(min_exp or 0.0, override_min)
            except (ValueError, TypeError):
                pass

        exp_range: Dict[str, Any] = {}
        if min_exp is not None:
            exp_range["gte"] = min_exp
        if max_exp is not None:
            exp_range["lt"] = max_exp

        if exp_range:
            filter_clauses.append({"range": {"experience_years": exp_range}})

        # 4. Job title matching across nested experience.title OR top-level education
        if requirements.job_title:
            title_str = requirements.job_title
            must_clauses.append({
                "bool": {
                    "should": [
                        {
                            "nested": {
                                "path": "experience",
                                "query": {
                                    "match": {
                                        "experience.title": {
                                            "query": title_str,
                                            "operator": "or"
                                        }
                                    }
                                }
                            }
                        },
                        {
                            "match": {
                                "education": {
                                    "query": title_str,
                                    "operator": "or"
                                }
                            }
                        }
                    ],
                    "minimum_should_match": 1
                }
            })

        bool_query: Dict[str, Any] = {}
        if filter_clauses:
            bool_query["filter"] = filter_clauses
        if must_clauses:
            bool_query["must"] = must_clauses

        if not bool_query:
            return {"match_all": {}}

        return {"bool": bool_query}

    def search_vector(
        self,
        query: str,
        requirements: ParsedRequirements,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Executes k-NN vector search using query embedding while respecting structured filters.
        Embeds semantic_query if present; falls back to original query text.
        """
        target_text = requirements.semantic_query or query
        query_vector = self.embedding_service.embed_text(target_text)

        # Build structured filter clauses to enforce alongside vector search
        base_query = self.build_opensearch_query(requirements, filters)
        filter_clauses = base_query.get("bool", {}).get("filter", [])

        knn_body: Dict[str, Any] = {
            "size": limit,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": query_vector,
                        "k": limit,
                    }
                }
            },
            "_source": True,
        }

        # Apply structured filters to k-NN query if present
        if filter_clauses:
            knn_body["query"]["knn"]["embedding"]["filter"] = {
                "bool": {"filter": filter_clauses}
            }

        try:
            response = self.client.search(index=self.index_name, body=knn_body)
            hits = response.get("hits", {}).get("hits", [])
            return hits
        except Exception as e:
            logger.warning("Vector search execution failed: %s. Returning empty vector hits.", str(e))
            return []

    async def search(
        self,
        query: str,
        page: int = 1,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        search_mode: str = "hybrid",
        rank: bool = False,
    ) -> SearchResponse:
        """
        Main search entry point supporting search_mode in ('bm25', 'vector', 'hybrid'),
        candidate feature ranking when rank=True, and Redis search & agent response caching.
        """
        # 1. Search Result Cache Check
        search_params = {
            "query": (query or "").strip().lower(),
            "page": page,
            "limit": limit,
            "filters": filters or {},
            "search_mode": search_mode,
            "rank": rank,
            "index_name": self.index_name,
        }
        search_cache_key = self.cache_service.make_search_key(search_params)
        cached_search_data = await self.cache_service.get(search_cache_key)
        if cached_search_data is not None:
            return SearchResponse(**cached_search_data)

        # 2. Agent Requirement Extraction Cache Check
        agent_cache_key = self.cache_service.make_agent_key(query or "")
        cached_reqs_data = await self.cache_service.get(agent_cache_key)
        if cached_reqs_data is not None:
            requirements = ParsedRequirements(**cached_reqs_data)
        else:
            requirements = HybridRequirementExtractor().extract(query)
            await self.cache_service.set(
                agent_cache_key,
                requirements.model_dump(mode="json"),
                ttl=self.cache_service.agent_ttl,
            )

        from_offset = (page - 1) * limit

        # If ranking is enabled, expand retrieval candidate pool limit
        if rank:
            pool_limit = max(limit * 5, int(os.getenv("RANKING_CANDIDATE_LIMIT", "200")))
            fetch_limit = pool_limit
            fetch_from = 0
        else:
            fetch_limit = limit
            fetch_from = from_offset

        bm25_hits: List[Dict[str, Any]] = []
        vector_hits: List[Dict[str, Any]] = []
        final_hits: List[Dict[str, Any]] = []
        total = 0

        # Execute requested search mode
        if search_mode == "bm25":
            opensearch_query = self.build_opensearch_query(requirements, filters)
            body = {
                "query": opensearch_query,
                "from": fetch_from,
                "size": fetch_limit,
                "sort": [{"candidate_id": {"order": "asc"}}],
                "track_total_hits": True,
            }
            res = self.client.search(index=self.index_name, body=body)
            hits_data = res.get("hits", {})
            total_info = hits_data.get("total", {})
            total = total_info.get("value", 0) if isinstance(total_info, dict) else int(total_info)
            final_hits = hits_data.get("hits", [])

        elif search_mode == "vector":
            vector_hits = self.search_vector(query, requirements, filters, limit=fetch_limit)
            total = len(vector_hits)
            final_hits = vector_hits

        else:
            # Default HYBRID Mode: BM25 + Vector + RRF Fusion with Fallback Resilience
            retrieve_limit = fetch_limit if rank else (limit * self.candidate_multiplier)

            # 1. Fetch BM25 Candidate Batch
            try:
                opensearch_query = self.build_opensearch_query(requirements, filters)
                body = {
                    "query": opensearch_query,
                    "from": 0,
                    "size": retrieve_limit,
                    "track_total_hits": True,
                }
                res = self.client.search(index=self.index_name, body=body)
                hits_data = res.get("hits", {})
                total_info = hits_data.get("total", {})
                total = total_info.get("value", 0) if isinstance(total_info, dict) else int(total_info)
                bm25_hits = hits_data.get("hits", [])
            except Exception as e:
                logger.warning("Hybrid BM25 phase failed: %s", str(e))
                bm25_hits = []

            # 2. Fetch Vector Candidate Batch
            try:
                vector_hits = self.search_vector(query, requirements, filters, limit=retrieve_limit)
            except Exception as e:
                logger.warning("Hybrid Vector phase failed: %s", str(e))
                vector_hits = []

            # 3. Apply Reciprocal Rank Fusion or Fallbacks
            if bm25_hits and vector_hits:
                fused = reciprocal_rank_fusion(
                    bm25_hits, vector_hits, rrf_k=self.rrf_k, top_k=retrieve_limit
                )
                final_hits = fused if rank else fused[from_offset : from_offset + limit]
            elif bm25_hits:
                logger.info("Hybrid search falling back to BM25-only")
                final_hits = bm25_hits if rank else bm25_hits[from_offset : from_offset + limit]
            elif vector_hits:
                logger.info("Hybrid search falling back to Vector-only")
                final_hits = vector_hits if rank else vector_hits[from_offset : from_offset + limit]
                total = len(vector_hits)
            else:
                final_hits = []

        pages = math.ceil(total / limit) if total > 0 else 0

        # Apply Ranking Layer if requested
        if rank and final_hits:
            ranking_service = CandidateRankingService()
            ranked_candidates = ranking_service.rank_candidates(
                hits=final_hits,
                requirements=requirements,
                top_k=limit,
            )
            candidates = [rc.candidate for rc in ranked_candidates]
        else:
            candidates: List[CandidateResponse] = []
            for hit in final_hits:
                source = hit.get("_source", {})
                candidate_id = source.get("candidate_id", hit.get("_id"))

                exp_raw = source.get("experience", [])
                cleaned_exp = []
                if isinstance(exp_raw, list):
                    for item in exp_raw:
                        if isinstance(item, dict) and item.get("company") and item.get("title"):
                            exp_item = dict(item)
                            sd = str(exp_item.get("start_date", ""))
                            if sd and (" " in sd or "T" in sd):
                                exp_item["start_date"] = sd.split(" ")[0].split("T")[0]
                            elif not sd:
                                exp_item["start_date"] = "2020-01-01"

                            ed = str(exp_item.get("end_date", ""))
                            if ed and (" " in ed or "T" in ed):
                                exp_item["end_date"] = ed.split(" ")[0].split("T")[0]
                            elif not ed or ed.lower() == "none":
                                exp_item["end_date"] = None
                            cleaned_exp.append(exp_item)

                cand_dict = {
                    "id": str(candidate_id),
                    "name": source.get("name", ""),
                    "email": source.get("email", ""),
                    "location": source.get("location", ""),
                    "experience_years": source.get("experience_years", 0.0),
                    "skills": source.get("skills", []),
                    "education": source.get("education", ""),
                    "experience": cleaned_exp,
                }
                candidates.append(CandidateResponse(**cand_dict))

        response = SearchResponse(
            query=query,
            parsed_requirements=requirements,
            results=candidates,
            limit=limit,
            pagination_mode=PaginationMode.OFFSET,
            total=total,
            page=page,
            pages=pages,
        )

        # 4. Store Search Result in Redis Cache
        await self.cache_service.set(
            search_cache_key,
            response.model_dump(mode="json"),
            ttl=self.cache_service.search_ttl,
        )

        return response
