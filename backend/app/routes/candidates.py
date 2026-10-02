from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.models.candidate import CandidateCreate, CandidateResponse, PaginatedCandidates
from app.services import candidate_service

router = APIRouter()


@router.post("", response_model=dict, status_code=201)
async def create_candidate(payload: CandidateCreate):
    candidate_id = await candidate_service.create_candidate(payload)
    return {"id": candidate_id}


@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(candidate_id: str):
    candidate = await candidate_service.get_candidate_by_id(candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@router.get("", response_model=PaginatedCandidates)
async def list_candidates(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    skill: Optional[str] = Query(None, description="Filter by skill"),
    location: Optional[str] = Query(None, description="Filter by location (case-insensitive)"),
    min_experience: Optional[float] = Query(None, ge=0, description="Minimum years of experience"),
):
    return await candidate_service.list_candidates(
        page=page,
        limit=limit,
        skill=skill,
        location=location,
        min_experience=min_experience,
    )
