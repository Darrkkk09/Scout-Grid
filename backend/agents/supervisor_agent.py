import asyncio
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from agents.query_expansion_agent import QueryExpansionAgent, ExpandedRequirements
from agents.candidate_verifier_agent import CandidateVerifierAgent, CandidateVerificationResult
from agents.outreach_agent import OutreachAgent, OutreachDraft
from services.cache_service import CacheService
from services.search_coordinator import SearchCoordinator

logger = logging.getLogger(__name__)


class VerifiedCandidateResult(BaseModel):
    candidate: Dict[str, Any]
    verification: CandidateVerificationResult
    outreach: Optional[OutreachDraft] = None


class SourcingPipelineResponse(BaseModel):
    query: str
    expanded_requirements: ExpandedRequirements
    total_found: int
    candidates: List[VerifiedCandidateResult] = Field(default_factory=list)


class SupervisorAgent:
    """
    Supervisor / Sourcing Pipeline Orchestrator Agent.
    Coordinates end-to-end multi-agent candidate sourcing:
    1. Query Expansion (QueryExpansionAgent)
    2. Hybrid Candidate Retrieval (SearchCoordinator)
    3. Parallel Candidate Auditing & Fit Verification (CandidateVerifierAgent)
    4. Candidate Engagement Outreach Generation (OutreachAgent)
    """

    def __init__(
        self,
        expansion_agent: Optional[QueryExpansionAgent] = None,
        verifier_agent: Optional[CandidateVerifierAgent] = None,
        outreach_agent: Optional[OutreachAgent] = None,
        search_coordinator: Optional[SearchCoordinator] = None,
        cache_service: Optional[CacheService] = None,
    ):
        self.expansion_agent = expansion_agent or QueryExpansionAgent()
        self.verifier_agent = verifier_agent or CandidateVerifierAgent()
        self.outreach_agent = outreach_agent or OutreachAgent()
        self.search_coordinator = search_coordinator or SearchCoordinator()
        self.cache_service = cache_service or CacheService()

    async def run(
        self,
        query: str,
        generate_outreach: bool = False,
        outreach_tone: str = "professional",
        top_k: int = 10,
    ) -> SourcingPipelineResponse:
        """Runs the entire 4-agent sourcing pipeline asynchronously."""
        if not query or not query.strip():
            return SourcingPipelineResponse(
                query="",
                expanded_requirements=ExpandedRequirements(original_query=""),
                total_found=0,
                candidates=[],
            )

        # 1. Query Expansion Agent
        expanded_reqs: ExpandedRequirements = await self.expansion_agent.run(query)

        # 2. OpenSearch Hybrid Retrieval via Search Coordinator
        search_results = await self.search_coordinator.search(
            query=query,
            skills=expanded_reqs.expanded_skills,
            location=expanded_reqs.location,
            min_experience=expanded_reqs.min_experience,
            max_experience=expanded_reqs.max_experience,
            size=top_k,
        )

        candidates_data = search_results.get("candidates", [])
        total_found = search_results.get("total", len(candidates_data))

        # Convert ParsedRequirements format for verifier
        from models.search import ParsedRequirements
        parsed_reqs = ParsedRequirements(
            skills=expanded_reqs.primary_skills or expanded_reqs.expanded_skills,
            location=expanded_reqs.location,
            min_experience=expanded_reqs.min_experience,
            max_experience=expanded_reqs.max_experience,
            job_title=expanded_reqs.job_title,
        )

        # 3. Parallel Candidate Verification and Outreach Generation
        verified_candidates: List[VerifiedCandidateResult] = []

        async def _process_candidate(cand: Dict[str, Any]) -> VerifiedCandidateResult:
            ver_task = self.verifier_agent.run(cand, parsed_reqs)
            out_task = (
                self.outreach_agent.run(
                    cand,
                    job_title=expanded_reqs.job_title or "Engineer",
                    tone=outreach_tone,
                )
                if generate_outreach
                else None
            )

            if out_task:
                verification, outreach = await asyncio.gather(ver_task, out_task)
            else:
                verification = await ver_task
                outreach = None

            return VerifiedCandidateResult(
                candidate=cand,
                verification=verification,
                outreach=outreach,
            )

        if candidates_data:
            verified_candidates = await asyncio.gather(
                *[_process_candidate(c) for c in candidates_data]
            )

        # Sort verified candidates by fit score descending
        verified_candidates.sort(key=lambda x: x.verification.fit_score, reverse=True)

        return SourcingPipelineResponse(
            query=query,
            expanded_requirements=expanded_reqs,
            total_found=total_found,
            candidates=verified_candidates,
        )
