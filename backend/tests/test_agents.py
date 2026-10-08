import pytest
from agents import (
    QueryExpansionAgent,
    CandidateVerifierAgent,
    OutreachAgent,
    SupervisorAgent,
)
from models.search import ParsedRequirements


@pytest.mark.asyncio
async def test_query_expansion_agent():
    agent = QueryExpansionAgent()
    res = await agent.run("Python developer in Bangalore with 3+ years experience")
    assert res.original_query == "Python developer in Bangalore with 3+ years experience"
    assert "Python" in res.expanded_skills
    assert "FastAPI" in res.expanded_skills or "Django" in res.expanded_skills


@pytest.mark.asyncio
async def test_candidate_verifier_agent():
    agent = CandidateVerifierAgent()
    candidate = {
        "id": "cand_123",
        "name": "Jane Doe",
        "skills": ["Python", "FastAPI", "PostgreSQL"],
        "experience_years": 4.5,
    }
    reqs = ParsedRequirements(skills=["Python", "FastAPI"], min_experience=3.0)

    result = await agent.run(candidate, reqs)
    assert result.candidate_id == "cand_123"
    assert result.fit_score > 70.0
    assert "Python" in result.matching_skills
    assert result.experience_match is True


@pytest.mark.asyncio
async def test_outreach_agent():
    agent = OutreachAgent()
    candidate = {
        "id": "cand_456",
        "name": "John Smith",
        "skills": ["React", "TypeScript"],
        "company": "TechCorp",
    }
    draft = await agent.run(candidate, job_title="Senior Frontend Lead", tone="casual")
    assert draft.candidate_id == "cand_456"
    assert draft.tone == "casual"
    assert "John" in draft.body
    assert "Senior Frontend Lead" in draft.subject or "Senior Frontend Lead" in draft.body


@pytest.mark.asyncio
async def test_supervisor_agent():
    supervisor = SupervisorAgent()
    res = await supervisor.run(
        query="Python engineer",
        generate_outreach=True,
        outreach_tone="professional",
        top_k=2,
    )
    assert res.query == "Python engineer"
    assert res.expanded_requirements is not None
    assert isinstance(res.candidates, list)
