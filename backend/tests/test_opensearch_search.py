from unittest.mock import MagicMock
import pytest

from models.search import ParsedRequirements
from services.opensearch_search_service import OpenSearchService


def test_build_opensearch_query_skills_and_location():
    service = OpenSearchService(client=MagicMock())
    reqs = ParsedRequirements(
        skills=["Python", "FastAPI"],
        location="Bangalore",
        min_experience=3.0,
        job_title=None,
    )
    query = service.build_opensearch_query(reqs)

    assert "bool" in query
    assert "filter" in query["bool"]
    filters = query["bool"]["filter"]

    assert {"term": {"skills": "Python"}} in filters
    assert {"term": {"skills": "FastAPI"}} in filters
    assert {"term": {"location": "Bangalore"}} in filters
    assert {"range": {"experience_years": {"gte": 3.0}}} in filters


def test_build_opensearch_query_job_title():
    service = OpenSearchService(client=MagicMock())
    reqs = ParsedRequirements(
        skills=[],
        location=None,
        min_experience=None,
        job_title="backend engineer",
    )
    query = service.build_opensearch_query(reqs)

    assert "bool" in query
    assert "must" in query["bool"]
    must_clause = query["bool"]["must"][0]

    assert "should" in must_clause["bool"]
    should_items = must_clause["bool"]["should"]
    assert len(should_items) == 2
    assert "nested" in should_items[0]
    assert should_items[0]["nested"]["path"] == "experience"
    assert "match" in should_items[1]
    assert "education" in should_items[1]["match"]


@pytest.mark.asyncio
async def test_opensearch_search_execution():
    mock_client = MagicMock()
    mock_client.search.return_value = {
        "hits": {
            "total": {"value": 1, "relation": "eq"},
            "hits": [
                {
                    "_id": "64a000000000000000000001",
                    "_source": {
                        "candidate_id": "64a000000000000000000001",
                        "name": "Jane Doe",
                        "email": "jane@example.com",
                        "location": "Bangalore",
                        "experience_years": 5.0,
                        "skills": ["Python", "FastAPI"],
                        "education": "B.Tech Computer Science",
                        "experience": [
                            {"company": "Acme", "title": "Senior Backend Engineer"}
                        ],
                    },
                }
            ],
        }
    }

    service = OpenSearchService(client=mock_client)
    res = await service.search(
        query="Python backend engineers with 3+ years in Bangalore",
        page=1,
        limit=20,
    )

    assert res.total == 1
    assert res.page == 1
    assert res.pages == 1
    assert len(res.results) == 1
    assert res.results[0].id == "64a000000000000000000001"
    assert res.results[0].name == "Jane Doe"
    assert res.results[0].location == "Bangalore"
    assert "Python" in res.results[0].skills
