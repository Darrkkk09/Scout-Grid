from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel

from app.database import get_candidates_collection

router = APIRouter()


class DashboardAnalyticsResponse(BaseModel):
    total_candidates: int


@router.get(
    "/dashboard",
    response_model=DashboardAnalyticsResponse,
    summary="Get dashboard analytics metrics",
    description="Returns aggregate metrics for the dashboard overview, including actual total candidate count in MongoDB.",
)
async def get_dashboard_analytics(
    collection: AsyncIOMotorCollection = Depends(get_candidates_collection),
) -> DashboardAnalyticsResponse:
    total = await collection.count_documents({})
    return DashboardAnalyticsResponse(total_candidates=total)
