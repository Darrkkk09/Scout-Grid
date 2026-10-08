import logging
from typing import Any, Dict, List, Optional

from database import get_candidates_collection
from services.opensearch_client import get_opensearch_client
from services.opensearch_search_service import OpenSearchService
from services.search_service import SearchService, _serialize_candidate_doc

logger = logging.getLogger(__name__)


class SearchCoordinator:
    """
    Unified Search Coordinator bridging OpenSearch and MongoDB fallback search.
    Provides a clean, unified search contract for agents and routes.
    """

    def __init__(self):
        pass

    async def search(
        self,
        query: str,
        skills: Optional[List[str]] = None,
        location: Optional[str] = None,
        min_experience: Optional[float] = None,
        max_experience: Optional[float] = None,
        size: int = 10,
    ) -> Dict[str, Any]:
        """
        Executes candidate retrieval using OpenSearch Hybrid BM25+Vector search,
        with automated fallback to MongoDB collection search if OpenSearch is unconfigured/unavailable.
        """
        try:
            client = get_opensearch_client()
            if client is not None:
                opensearch_service = OpenSearchService(client)

                response = await opensearch_service.search_opensearch(
                    query=query,
                    size=size,
                    filters=None,  # Rely on BM25 + Vector semantic query matching without restricting to strict term filters
                    enable_hybrid=True,
                )
                
                # Transform results into unified dict format
                candidates = []
                for cand in response.results:
                    candidates.append(cand.model_dump(mode="json"))
                
                if candidates:
                    return {
                        "total": response.total,
                        "candidates": candidates,
                        "mode": "opensearch_hybrid",
                    }
        except Exception as e:
            logger.warning("OpenSearch search failed in coordinator, falling back to MongoDB: %s", str(e))

        # Fallback: MongoDB Search
        try:
            collection = get_candidates_collection()
            if collection is not None:
                search_service = SearchService(collection)
                response = await search_service.search(query=query, page=1, limit=size)
                candidates = [c.model_dump(mode="json") for c in response.results]
                
                # If requirements filter yielded zero hits in MongoDB, fallback to soft skills OR regex match
                if not candidates and skills:
                    logger.info("MongoDB exact requirement filter returned 0 docs, attempting soft skill search...")
                    filter_or = [{"skills": {"$regex": s, "$options": "i"}} for s in skills]
                    cursor = collection.find({"$or": filter_or}).limit(size)
                    raw_docs = await cursor.to_list(length=size)
                    candidates = [_serialize_candidate_doc(d).model_dump(mode="json") for d in raw_docs]

                return {
                    "total": len(candidates),
                    "candidates": candidates,
                    "mode": "mongodb_fallback",
                }
        except Exception as fallback_err:
            logger.error("MongoDB fallback search failed: %s", str(fallback_err), exc_info=True)

        return {
            "total": 0,
            "candidates": [],
            "mode": "none",
        }
