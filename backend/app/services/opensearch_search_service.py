import math
import logging
from typing import Any, Dict, List, Optional
from opensearchpy import OpenSearch

from app.models.candidate import CandidateResponse
from app.models.search import (
    PaginationMode,
    ParsedRequirements,
    SearchRequest,
    SearchResponse,
)
from app.services.opensearch_index import CANDIDATES_INDEX_NAME
from app.services.requirement_extractor import RequirementExtractor

logger = logging.getLogger(__name__)


class OpenSearchService:
    """
    Candidate Search Service using OpenSearch.
    Translates extracted query requirements and filter overrides into structured
    OpenSearch bool queries using term, terms, match, range, and nested clauses.
    """

    def __init__(self, client: OpenSearch, index_name: str = CANDIDATES_INDEX_NAME):
        self.client = client
        self.index_name = index_name

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

    async def search(
        self,
        query: str,
        page: int = 1,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> SearchResponse:
        requirements = RequirementExtractor.extract(query)
        opensearch_query = self.build_opensearch_query(requirements, filters)

        from_offset = (page - 1) * limit

        body = {
            "query": opensearch_query,
            "from": from_offset,
            "size": limit,
            "sort": [{"candidate_id": {"order": "asc"}}],
            "track_total_hits": True,
        }

        response = self.client.search(index=self.index_name, body=body)

        hits_data = response.get("hits", {})
        total_info = hits_data.get("total", {})
        total = total_info.get("value", 0) if isinstance(total_info, dict) else int(total_info)

        pages = math.ceil(total / limit) if total > 0 else 0

        candidates: List[CandidateResponse] = []
        for hit in hits_data.get("hits", []):
            source = hit.get("_source", {})
            # Map OpenSearch candidate_id back to candidate id expected by CandidateResponse
            candidate_id = source.get("candidate_id", hit.get("_id"))
            
            exp_raw = source.get("experience", [])
            cleaned_exp = []
            if isinstance(exp_raw, list):
                for item in exp_raw:
                    if isinstance(item, dict) and item.get("company") and item.get("title"):
                        exp_item = dict(item)
                        if not exp_item.get("start_date"):
                            exp_item["start_date"] = "2020-01-01"
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

        return SearchResponse(
            query=query,
            parsed_requirements=requirements,
            results=candidates,
            limit=limit,
            pagination_mode=PaginationMode.OFFSET,
            total=total,
            page=page,
            pages=pages,
        )
