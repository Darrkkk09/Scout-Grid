from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from motor.motor_asyncio import AsyncIOMotorCollection
from opensearchpy import OpenSearch

from database import get_candidates_collection
from models.search import SearchRequest, SearchResponse
from services.opensearch_client import get_opensearch_client
from services.opensearch_search_service import OpenSearchService
from services.search_service import SearchService

router = APIRouter()


@router.post(
    "",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search candidates via natural language query (MongoDB)",
    description="Extracts search requirements from query text and returns matching candidates from MongoDB.",
)
async def search_candidates(
    request: SearchRequest,
    page: Optional[int] = Query(None, ge=1),
    limit: Optional[int] = Query(None, ge=1, le=100),
    collection: AsyncIOMotorCollection = Depends(get_candidates_collection),
) -> SearchResponse:
    # Allow URL query param pagination to override body pagination if provided
    effective_page = page if page is not None else request.page
    effective_limit = limit if limit is not None else request.limit

    service = SearchService(collection)
    return await service.search(
        query=request.query,
        page=effective_page,
        limit=effective_limit,
        filters=request.filters,
        pagination_mode=request.pagination_mode,
        cursor_token=request.cursor,
    )


@router.post(
    "/opensearch",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search candidates via natural language query (OpenSearch)",
    description="Extracts search requirements from query text and returns matching candidates from OpenSearch using BM25, vector, or hybrid RRF search.",
)
async def search_candidates_opensearch(
    request: SearchRequest,
    page: Optional[int] = Query(None, ge=1),
    limit: Optional[int] = Query(None, ge=1, le=100),
    search_mode: str = Query("hybrid", description="Search mode: 'hybrid' (default), 'bm25', or 'vector'"),
    rank: bool = Query(False, description="Enable candidate feature ranking"),
    client: OpenSearch = Depends(get_opensearch_client),
) -> SearchResponse:
    effective_page = page if page is not None else request.page
    effective_limit = limit if limit is not None else request.limit
    effective_rank = rank or request.rank

    service = OpenSearchService(client)
    return await service.search(
        query=request.query,
        page=effective_page,
        limit=effective_limit,
        filters=request.filters,
        search_mode=search_mode,
        rank=effective_rank,
    )


