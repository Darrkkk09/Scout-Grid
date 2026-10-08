import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from models.search import ParsedRequirements
from services.cache_service import CacheService
from services.hybrid_requirement_extractor import HybridRequirementExtractor

logger = logging.getLogger(__name__)

# Core Technology Skill Graph Expansion Taxonomy
SKILL_TAXONOMY_MAP = {
    "python": ["Python", "FastAPI", "Django", "Flask", "PyTest", "PostgreSQL", "AsyncIO"],
    "react": ["React", "TypeScript", "Next.js", "Redux", "Tailwind CSS", "JavaScript"],
    "devops": ["Docker", "Kubernetes", "AWS", "CI/CD", "Terraform", "Linux"],
    "java": ["Java", "Spring Boot", "Microservices", "Kafka", "Maven", "Hibernate"],
    "node": ["Node.js", "Express.js", "TypeScript", "MongoDB", "REST API"],
    "data engineer": ["Spark", "Python", "SQL", "Hadoop", "Airflow", "Kafka"],
    "machine learning": ["Python", "PyTorch", "TensorFlow", "Scikit-Learn", "OpenCV", "Pandas"],
}


class ExpandedRequirements(BaseModel):
    original_query: str
    primary_skills: List[str] = Field(default_factory=list)
    expanded_skills: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    min_experience: Optional[float] = None
    max_experience: Optional[float] = None
    job_title: Optional[str] = None
    semantic_query: Optional[str] = None


class QueryExpansionAgent:
    """
    Skill Graph & Query Expansion Agent.
    Expands recruiter search queries using technical taxonomy mapping
    and caches expanded query objects in Redis under scoutgrid:agent:expansion:{hash}.
    """

    def __init__(
        self,
        extractor: Optional[HybridRequirementExtractor] = None,
        cache_service: Optional[CacheService] = None,
    ):
        self.extractor = extractor or HybridRequirementExtractor()
        self.cache_service = cache_service or CacheService()

    def _expand_skills(self, skills: List[str], query: str) -> List[str]:
        """Expands core skills using technology taxonomy graph."""
        expanded_set = set(skills)
        query_clean = query.lower()

        for key, exp_list in SKILL_TAXONOMY_MAP.items():
            if key in query_clean or any(key in s.lower() for s in skills):
                for sk in exp_list:
                    expanded_set.add(sk)

        return list(expanded_set)

    async def run(self, query: str) -> ExpandedRequirements:
        """
        Executes query expansion and returns ExpandedRequirements model.
        Leverages Redis caching for sub-10ms response on repeated query expansions.
        """
        if not query or not query.strip():
            return ExpandedRequirements(original_query="")

        # 1. Check Redis Cache
        cache_key = f"scoutgrid:agent:expansion:{self.cache_service.generate_hash(query.strip().lower())}"
        cached_val = await self.cache_service.get(cache_key)
        if cached_val is not None:
            logger.info("AGENT CACHE HIT (QueryExpansionAgent) query='%s'", query)
            return ExpandedRequirements(**cached_val)

        # 2. Extract Base Requirements using Hybrid Extractor (LLM / Fallback)
        parsed_reqs: ParsedRequirements = self.extractor.extract(query)

        # 3. Apply Tech Graph Skill Expansion
        expanded_skills = self._expand_skills(parsed_reqs.skills, query)

        result = ExpandedRequirements(
            original_query=query,
            primary_skills=parsed_reqs.skills,
            expanded_skills=expanded_skills,
            location=parsed_reqs.location,
            min_experience=parsed_reqs.min_experience,
            max_experience=parsed_reqs.max_experience,
            job_title=parsed_reqs.job_title,
            semantic_query=parsed_reqs.semantic_query,
        )

        # 4. Cache in Redis
        await self.cache_service.set(
            cache_key,
            result.model_dump(mode="json"),
            ttl=self.cache_service.agent_ttl,
        )

        return result
