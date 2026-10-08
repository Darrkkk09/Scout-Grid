import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from agents.supervisor_agent import SupervisorAgent, SourcingPipelineResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["Multi-Agent System"])


class SourcingRequest(BaseModel):
    query: str = Field(..., description="Recruiter natural language query")
    generate_outreach: bool = Field(False, description="Generate tailored outreach draft for candidate")
    outreach_tone: str = Field("professional", description="Outreach tone: professional, casual, or technical")
    top_k: int = Field(10, description="Max candidates to retrieve and audit")


@router.post("/sourcing", response_model=SourcingPipelineResponse)
async def run_sourcing_pipeline(request: SourcingRequest):
    """
    Triggers the Multi-Agent Sourcing Pipeline:
    1. Query Expansion Agent (Skill Graph & Term Taxonomy)
    2. Hybrid Candidate Search (BM25 + Vector RRF)
    3. Candidate Verifier Agent (Fit Score & Skill Audit)
    4. Outreach Agent (Personalized Engagement Draft)
    """
    try:
        supervisor = SupervisorAgent()
        response = await supervisor.run(
            query=request.query,
            generate_outreach=request.generate_outreach,
            outreach_tone=request.outreach_tone,
            top_k=request.top_k,
        )
        return response
    except Exception as e:
        logger.error("Error executing sourcing pipeline: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Sourcing pipeline failed: {str(e)}")
