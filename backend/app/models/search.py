from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.models.candidate import CandidateResponse


class PaginationMode(str, Enum):
    OFFSET = "offset"
    CURSOR = "cursor"


class ParsedRequirements(BaseModel):
    skills: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    min_experience: Optional[float] = None
    max_experience: Optional[float] = None
    job_title: Optional[str] = None
    semantic_query: Optional[str] = Field(
        default=None,
        description="Semantic context or intent for non-exact skill requirements"
    )


class SearchRequest(BaseModel):
    query: str = Field(..., description="Natural language search query")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)
    filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional explicit filter overrides (e.g. skill, location, min_experience)"
    )
    pagination_mode: PaginationMode = Field(
        default=PaginationMode.OFFSET,
        description="Pagination strategy: 'offset' (default) or 'cursor'"
    )
    cursor: Optional[str] = Field(
        default=None,
        description="Opaque base64 encoded cursor token for cursor pagination"
    )


class SearchResponse(BaseModel):
    query: str
    parsed_requirements: ParsedRequirements
    results: List[CandidateResponse]
    limit: int
    pagination_mode: PaginationMode = PaginationMode.OFFSET

    # Offset pagination fields (populated when pagination_mode == OFFSET)
    total: Optional[int] = None
    page: Optional[int] = None
    pages: Optional[int] = None

    # Cursor pagination fields (populated when pagination_mode == CURSOR)
    has_next_page: Optional[bool] = None
    next_cursor: Optional[str] = None

