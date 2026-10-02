from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class ExperienceEntry(BaseModel):
    company: str
    title: str
    start_date: date
    end_date: Optional[date] = None
    description: Optional[str] = None


class CandidateCreate(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    location: str = Field(..., min_length=1)
    experience_years: float = Field(..., ge=0)
    skills: list[str] = Field(..., min_length=1)
    education: str
    experience: list[ExperienceEntry] = Field(default_factory=list)


class CandidateResponse(BaseModel):
    id: str
    name: str
    email: str
    location: str
    experience_years: float
    skills: list[str]
    education: str
    experience: list[ExperienceEntry]


class PaginatedCandidates(BaseModel):
    total: int
    page: int
    limit: int
    pages: int
    candidates: list[CandidateResponse]
