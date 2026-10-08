import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from models.search import ParsedRequirements
from services.cache_service import CacheService

logger = logging.getLogger(__name__)


class CandidateVerificationResult(BaseModel):
    candidate_id: str
    fit_score: float = Field(..., description="Fit score from 0.0 to 100.0")
    matching_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    experience_match: bool = True
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    fit_summary: str = ""


class CandidateVerifierAgent:
    """
    Candidate Verifier & Fit Audit Agent.
    Audits retrieved candidate profiles against search requirements,
    computing fit score, skill matches, experience suitability, and key strengths.
    Caches verified results in Redis under scoutgrid:agent:verifier:{hash}.
    """

    def __init__(self, cache_service: Optional[CacheService] = None):
        self.cache_service = cache_service or CacheService()

    def verify(
        self, candidate: Dict[str, Any], requirements: ParsedRequirements
    ) -> CandidateVerificationResult:
        """Audits candidate profile synchronously against requirements."""
        cand_id = str(candidate.get("id") or candidate.get("_id") or "unknown")
        cand_skills = [
            s.strip().lower() for s in candidate.get("skills", []) if isinstance(s, str)
        ]
        required_skills = [s.strip().lower() for s in requirements.skills]

        matching = []
        missing = []
        for req in required_skills:
            if any(req in cs for cs in cand_skills):
                matching.append(req.title())
            else:
                missing.append(req.title())

        cand_exp = candidate.get("experience_years") or candidate.get("experience", 0)
        try:
            cand_exp = float(cand_exp)
        except (ValueError, TypeError):
            cand_exp = 0.0

        min_exp = requirements.min_experience or 0.0
        exp_match = cand_exp >= min_exp

        # Compute Fit Score (Base 50, +30 for skill ratio, +20 for experience match)
        skill_score = (
            (len(matching) / len(required_skills) * 40.0) if required_skills else 40.0
        )
        exp_score = 30.0 if exp_match else max(0.0, 30.0 - (min_exp - cand_exp) * 10)
        base_quality = 30.0 if candidate.get("experience_years") else 20.0
        fit_score = round(min(100.0, skill_score + exp_score + base_quality), 1)

        strengths = []
        if matching:
            strengths.append(f"Strong match in core skills: {', '.join(matching)}")
        if exp_match:
            strengths.append(f"Meets minimum experience threshold ({cand_exp} yrs)")
        if not strengths:
            strengths.append("General technical background")

        gaps = []
        if missing:
            gaps.append(f"Missing explicitly required skills: {', '.join(missing)}")
        if not exp_match:
            gaps.append(
                f"Experience ({cand_exp} yrs) is below requested minimum ({min_exp} yrs)"
            )

        summary = (
            f"Candidate evaluated with {fit_score}% fit score. "
            f"Matched {len(matching)}/{len(required_skills) if required_skills else 0} skills."
        )

        return CandidateVerificationResult(
            candidate_id=cand_id,
            fit_score=fit_score,
            matching_skills=matching,
            missing_skills=missing,
            experience_match=exp_match,
            strengths=strengths,
            gaps=gaps,
            fit_summary=summary,
        )

    async def run(
        self, candidate: Dict[str, Any], requirements: ParsedRequirements
    ) -> CandidateVerificationResult:
        """
        Runs candidate verification with Redis sub-agent caching.
        """
        cand_id = str(candidate.get("id") or candidate.get("_id") or "unknown")
        req_hash = self.cache_service.generate_hash(
            f"{cand_id}:{requirements.skills}:{requirements.min_experience}"
        )
        cache_key = f"scoutgrid:agent:verifier:{req_hash}"

        cached_val = await self.cache_service.get(cache_key)
        if cached_val is not None:
            logger.info("AGENT CACHE HIT (CandidateVerifierAgent) candidate_id=%s", cand_id)
            return CandidateVerificationResult(**cached_val)

        result = self.verify(candidate, requirements)

        await self.cache_service.set(
            cache_key,
            result.model_dump(mode="json"),
            ttl=self.cache_service.agent_ttl,
        )

        return result
