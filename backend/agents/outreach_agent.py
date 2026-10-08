import logging
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from services.cache_service import CacheService

logger = logging.getLogger(__name__)


class OutreachDraft(BaseModel):
    candidate_id: str
    tone: str = "professional"
    subject: str
    body: str


class OutreachAgent:
    """
    Personalized Candidate Engagement & Outreach Agent.
    Generates tailored recruiter emails / InMail drafts based on candidate profiles,
    verified skills, and recruiter role requirements.
    Caches outreach drafts in Redis under scoutgrid:agent:outreach:{hash}.
    """

    def __init__(self, cache_service: Optional[CacheService] = None):
        self.cache_service = cache_service or CacheService()

    def generate_draft(
        self,
        candidate: Dict[str, Any],
        job_title: str = "Senior Engineer",
        tone: str = "professional",
    ) -> OutreachDraft:
        """Generates candidate outreach text synchronously."""
        cand_id = str(candidate.get("id") or candidate.get("_id") or "unknown")
        name = candidate.get("name") or candidate.get("full_name") or "there"
        first_name = name.split()[0] if name else "there"
        skills = candidate.get("skills", [])
        top_skills = ", ".join(skills[:3]) if skills else "your technical stack"
        company = candidate.get("company") or "your current organization"

        if tone == "casual":
            subject = f"Exciting {job_title} opportunity!"
            body = (
                f"Hi {first_name},\n\n"
                f"Hope you're having a great week! I came across your background at {company} and was super impressed "
                f"by your work with {top_skills}.\n\n"
                f"We're currently building out our engineering team and are looking for a {job_title}. "
                f"Would love to connect for a quick 10-minute casual chat to explore possibilities.\n\n"
                f"Best,\nScoutGrid Recruiting Team"
            )
        elif tone == "technical":
            subject = f"Engineering query regarding {top_skills} & {job_title} role"
            body = (
                f"Hello {first_name},\n\n"
                f"I was reviewing your technical profile and noticed your strong expertise in {top_skills}. "
                f"Given your background at {company}, your experience aligns closely with complex engineering challenges we're tackling.\n\n"
                f"We're actively recruiting a {job_title} to lead system architecture and search performance. "
                f"If open to exploring next steps, let's schedule a brief technical intro.\n\n"
                f"Regards,\nScoutGrid Engineering Talent Team"
            )
        else:  # professional
            subject = f"Career Opportunity: {job_title} Role"
            body = (
                f"Dear {first_name},\n\n"
                f"I hope this message finds you well. I was reviewing your impressive candidate profile and experience "
                f"with {top_skills} at {company}.\n\n"
                f"Our organization is currently hiring for a {job_title} position, and we believe your skills and career trajectory "
                f"make you an exceptional candidate for this role.\n\n"
                f"Would you be available for a brief conversation this week to discuss how this opportunity aligns with your goals?\n\n"
                f"Sincerely,\nScoutGrid Sourcing Team"
            )

        return OutreachDraft(
            candidate_id=cand_id,
            tone=tone,
            subject=subject,
            body=body,
        )

    async def run(
        self,
        candidate: Dict[str, Any],
        job_title: str = "Senior Engineer",
        tone: str = "professional",
    ) -> OutreachDraft:
        """
        Executes outreach draft generation with Redis sub-agent caching.
        """
        cand_id = str(candidate.get("id") or candidate.get("_id") or "unknown")
        cache_key = f"scoutgrid:agent:outreach:{self.cache_service.generate_hash(f'{cand_id}:{job_title}:{tone}')}"

        cached_val = await self.cache_service.get(cache_key)
        if cached_val is not None:
            logger.info("AGENT CACHE HIT (OutreachAgent) candidate_id=%s tone=%s", cand_id, tone)
            return OutreachDraft(**cached_val)

        result = self.generate_draft(candidate, job_title=job_title, tone=tone)

        await self.cache_service.set(
            cache_key,
            result.model_dump(mode="json"),
            ttl=self.cache_service.agent_ttl,
        )

        return result
