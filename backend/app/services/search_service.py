import base64
import json
import math
import re
from typing import Any, Dict, List, Optional, Tuple

from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorCollection

from app.models.candidate import CandidateResponse
from app.models.search import (
    PaginationMode,
    ParsedRequirements,
    SearchRequest,
    SearchResponse,
)
from app.services.requirement_extractor import RequirementExtractor


def encode_cursor(doc_id: str) -> str:
    """Encode string document ID into base64 url-safe token."""
    payload = json.dumps({"id": str(doc_id)})
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("utf-8")


def decode_cursor(token: str) -> str:
    """Decode token to document ID or raise HTTP 400 Bad Request."""
    try:
        raw = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
        data = json.loads(raw)
        doc_id = data.get("id")
        if not doc_id:
            raise ValueError("Missing 'id' in cursor payload")
        return str(doc_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid pagination cursor token: {str(e)}",
        )


class SearchService:
    """
    Candidate Search Service isolated for ScoutGrid.
    Constructs MongoDB query filters directly from extracted query requirements
    and optional user UI filter overrides, supporting both Offset and Cursor pagination.
    """

    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    def build_mongo_query(
        self,
        requirements: ParsedRequirements,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        mongo_filter: Dict[str, Any] = {}

        # 1. Skills matching (Require ALL extracted skills using $all)
        combined_skills = list(requirements.skills)
        if filters and filters.get("skill"):
            override_skill = str(filters["skill"]).strip()
            if override_skill and override_skill not in combined_skills:
                combined_skills.append(override_skill)

        if len(combined_skills) == 1:
            mongo_filter["skills"] = combined_skills[0]
        elif len(combined_skills) > 1:
            mongo_filter["skills"] = {"$all": combined_skills}

        # 2. Location filter (case-insensitive regex for flexibility)
        location = (filters.get("location") if filters else None) or requirements.location
        if location and str(location).strip():
            loc_str = str(location).strip()
            mongo_filter["location"] = {"$regex": f"^{re.escape(loc_str)}$", "$options": "i"}

        # 3. Experience years range filter ($gte / $lt)
        min_exp = requirements.min_experience
        max_exp = requirements.max_experience

        if filters and filters.get("min_experience") is not None:
            try:
                override_min = float(filters["min_experience"])
                min_exp = max(min_exp or 0.0, override_min)
            except (ValueError, TypeError):
                pass

        exp_query: Dict[str, Any] = {}
        if min_exp is not None:
            exp_query["$gte"] = min_exp
        if max_exp is not None:
            exp_query["$lt"] = max_exp

        if exp_query:
            mongo_filter["experience_years"] = exp_query

        # 4. Job title matching across work history title or education
        if requirements.job_title:
            title_regex = re.escape(requirements.job_title)
            mongo_filter["$or"] = [
                {"experience.title": {"$regex": title_regex, "$options": "i"}},
                {"education": {"$regex": title_regex, "$options": "i"}},
            ]

        return mongo_filter

    async def search(
        self,
        query: str,
        page: int = 1,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        pagination_mode: PaginationMode = PaginationMode.OFFSET,
        cursor_token: Optional[str] = None,
    ) -> SearchResponse:
        # Extract structured criteria
        requirements = RequirementExtractor.extract(query)

        # Build base MongoDB query filter
        base_filter = self.build_mongo_query(requirements, filters)

        if pagination_mode == PaginationMode.CURSOR:
            return await self._search_cursor(
                query=query,
                requirements=requirements,
                base_filter=base_filter,
                limit=limit,
                cursor_token=cursor_token,
            )

        # Default OFFSET pagination path
        return await self._search_offset(
            query=query,
            requirements=requirements,
            base_filter=base_filter,
            page=page,
            limit=limit,
        )

    async def _search_offset(
        self,
        query: str,
        requirements: ParsedRequirements,
        base_filter: Dict[str, Any],
        page: int,
        limit: int,
    ) -> SearchResponse:
        total = await self.collection.count_documents(base_filter)
        pages = math.ceil(total / limit) if total > 0 else 0

        skip = (page - 1) * limit
        cursor = self.collection.find(base_filter).sort("_id", 1).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)

        candidates: List[CandidateResponse] = []
        for doc in docs:
            doc["id"] = str(doc.get("_id", doc.get("id")))
            candidates.append(CandidateResponse(**doc))

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

    async def _search_cursor(
        self,
        query: str,
        requirements: ParsedRequirements,
        base_filter: Dict[str, Any],
        limit: int,
        cursor_token: Optional[str],
    ) -> SearchResponse:
        # Copy base filter to avoid mutating shared state
        query_filter = dict(base_filter)

        if cursor_token:
            last_id_str = decode_cursor(cursor_token)
            if ObjectId.is_valid(last_id_str):
                query_filter["_id"] = {"$gt": ObjectId(last_id_str)}
            else:
                query_filter["_id"] = {"$gt": last_id_str}

        # Query limit + 1 documents without calling count_documents()
        cursor = self.collection.find(query_filter).sort("_id", 1).limit(limit + 1)
        docs = await cursor.to_list(length=limit + 1)

        has_next_page = len(docs) > limit
        result_docs = docs[:limit]

        next_cursor_str = None
        candidates: List[CandidateResponse] = []

        for doc in result_docs:
            doc_id = str(doc.get("_id", doc.get("id")))
            doc["id"] = doc_id
            candidates.append(CandidateResponse(**doc))

        if has_next_page and candidates:
            next_cursor_str = encode_cursor(candidates[-1].id)

        return SearchResponse(
            query=query,
            parsed_requirements=requirements,
            results=candidates,
            limit=limit,
            pagination_mode=PaginationMode.CURSOR,
            has_next_page=has_next_page,
            next_cursor=next_cursor_str,
        )

