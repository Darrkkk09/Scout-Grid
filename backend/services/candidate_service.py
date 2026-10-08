import math
from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ASCENDING

from database import get_candidates_collection
from models.candidate import CandidateCreate, CandidateResponse, PaginatedCandidates


from datetime import datetime, date


def _clean_experience(exp_list: list) -> list:
    cleaned = []
    if isinstance(exp_list, list):
        for item in exp_list:
            if isinstance(item, dict):
                entry = dict(item)
                # Ensure start_date is a date object (no time)
                sd = entry.get("start_date")
                if isinstance(sd, datetime):
                    entry["start_date"] = sd.date()
                elif isinstance(sd, str):
                    try:
                        entry["start_date"] = date.fromisoformat(sd.split("T")[0])
                    except Exception:
                        entry["start_date"] = date(2020, 1, 1)
                
                # Ensure end_date is a date object or None
                ed = entry.get("end_date")
                if isinstance(ed, datetime):
                    entry["end_date"] = ed.date()
                elif isinstance(ed, str):
                    try:
                        entry["end_date"] = date.fromisoformat(ed.split("T")[0])
                    except Exception:
                        entry["end_date"] = None
                
                cleaned.append(entry)
    return cleaned


def _serialize(doc: dict) -> CandidateResponse:
    """Convert a MongoDB document to a CandidateResponse."""
    return CandidateResponse(
        id=str(doc["_id"]),
        name=doc.get("name", ""),
        email=doc.get("email", ""),
        location=doc.get("location", ""),
        experience_years=doc.get("experience_years", 0.0),
        skills=doc.get("skills", []),
        education=doc.get("education", ""),
        experience=_clean_experience(doc.get("experience", [])),
    )


async def create_candidate(data: CandidateCreate) -> str:
    collection = get_candidates_collection()
    doc = data.model_dump(mode="json")
    result = await collection.insert_one(doc)
    return str(result.inserted_id)


async def get_candidate_by_id(candidate_id: str) -> Optional[CandidateResponse]:
    try:
        oid = ObjectId(candidate_id)
    except InvalidId:
        return None

    collection = get_candidates_collection()
    doc = await collection.find_one({"_id": oid})
    if doc is None:
        return None
    return _serialize(doc)


async def list_candidates(
    page: int,
    limit: int,
    skill: Optional[str] = None,
    location: Optional[str] = None,
    min_experience: Optional[float] = None,
) -> PaginatedCandidates:
    collection = get_candidates_collection()

    query: dict = {}
    if skill:
        query["skills"] = skill
    if location:
        query["location"] = {"$regex": location, "$options": "i"}
    if min_experience is not None:
        query["experience_years"] = {"$gte": min_experience}

    total = await collection.count_documents(query)
    pages = math.ceil(total / limit) if total > 0 else 1
    skip = (page - 1) * limit

    cursor = (
        collection.find(query)
        .sort("_id", ASCENDING)
        .skip(skip)
        .limit(limit)
    )

    candidates = [_serialize(doc) async for doc in cursor]

    return PaginatedCandidates(
        total=total,
        page=page,
        limit=limit,
        pages=pages,
        candidates=candidates,
    )
