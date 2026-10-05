import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.models.candidate import CandidateResponse
from app.models.search import ParsedRequirements, SearchResponse
from app.services.cache_service import CacheService
from app.services.opensearch_search_service import OpenSearchService


@pytest.fixture
def cache_service():
    return CacheService()


def test_cache_key_generation(cache_service):
    # Distinct parameters must create distinct cache keys
    key1 = cache_service.make_search_key({"query": "python", "location": "Bangalore"})
    key2 = cache_service.make_search_key({"query": "python", "location": "Hyderabad"})
    key3 = cache_service.make_search_key({"query": "python", "location": "Bangalore"})

    assert key1 != key2
    assert key1 == key3
    assert key1.startswith("scoutgrid:search:")

    agent_key1 = cache_service.make_agent_key("Python Engineer")
    agent_key2 = cache_service.make_agent_key("python engineer")
    assert agent_key1 == agent_key2
    assert agent_key1.startswith("scoutgrid:agent:")


@pytest.mark.asyncio
async def test_redis_unreachable_fallback(cache_service):
    # Simulate Redis connection failure
    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(side_effect=ConnectionError("Redis offline"))
    mock_redis.set = AsyncMock(side_effect=ConnectionError("Redis offline"))

    cache_service._client = mock_redis

    # Operations should handle errors gracefully and return None/False without crashing
    val = await cache_service.get("test_key")
    assert val is None

    success = await cache_service.set("test_key", {"data": 123})
    assert success is False


@pytest.mark.asyncio
async def test_search_cache_hit_miss_flow():
    # Mock OpenSearch client and CacheService
    mock_opensearch_client = MagicMock()
    mock_cache_service = MagicMock(spec=CacheService)

    # First request: Cache MISS
    mock_cache_service.get = AsyncMock(return_value=None)
    mock_cache_service.set = AsyncMock(return_value=True)
    mock_cache_service.make_search_key.return_value = "scoutgrid:search:mockkey"
    mock_cache_service.make_agent_key.return_value = "scoutgrid:agent:mockkey"
    mock_cache_service.search_ttl = 600
    mock_cache_service.agent_ttl = 1800

    mock_search_res = {
        "took": 10,
        "timed_out": False,
        "hits": {
            "total": {"value": 1},
            "hits": [
                {
                    "_id": "c1",
                    "_score": 1.0,
                    "_source": {
                        "candidate_id": "c1",
                        "name": "Cached Alice",
                        "email": "alice@test.com",
                        "location": "Bangalore",
                        "experience_years": 5.0,
                        "skills": ["Python"],
                        "education": "CS",
                        "experience": [],
                    },
                }
            ],
        },
    }
    mock_opensearch_client.search.return_value = mock_search_res

    service = OpenSearchService(
        client=mock_opensearch_client,
        cache_service=mock_cache_service,
    )

    # 1. Execute Search -> MISS -> calls OpenSearch
    res1 = await service.search(query="Python", search_mode="bm25")
    assert len(res1.results) == 1
    assert res1.results[0].name == "Cached Alice"
    assert mock_opensearch_client.search.call_count == 1
    assert mock_cache_service.set.call_count >= 1

    # 2. Second request: Cache HIT -> returns cached result without calling OpenSearch
    cached_dict = res1.model_dump(mode="json")
    mock_cache_service.get = AsyncMock(return_value=cached_dict)

    res2 = await service.search(query="Python", search_mode="bm25")
    assert len(res2.results) == 1
    assert res2.results[0].name == "Cached Alice"
    # OpenSearch search count should still be 1 (NOT called again!)
    assert mock_opensearch_client.search.call_count == 1


@pytest.mark.asyncio
async def test_agent_cache_hit_miss_flow():
    mock_opensearch_client = MagicMock()
    mock_cache_service = MagicMock(spec=CacheService)

    mock_cache_service.make_search_key.return_value = "scoutgrid:search:key"
    mock_cache_service.make_agent_key.return_value = "scoutgrid:agent:reqkey"
    mock_cache_service.search_ttl = 600
    mock_cache_service.agent_ttl = 1800

    # Search cache MISS, Agent cache HIT
    mock_cache_service.get = AsyncMock(side_effect=[
        None,  # Search cache miss
        {"skills": ["CachedPython"], "location": "Bangalore", "min_experience": 4.0},  # Agent cache hit
    ])
    mock_cache_service.set = AsyncMock(return_value=True)
    mock_opensearch_client.search.return_value = {"hits": {"total": 0, "hits": []}}

    service = OpenSearchService(
        client=mock_opensearch_client,
        cache_service=mock_cache_service,
    )

    res = await service.search(query="Python Developer", search_mode="bm25")
    assert res.parsed_requirements.skills == ["CachedPython"]
    assert res.parsed_requirements.location == "Bangalore"
    assert res.parsed_requirements.min_experience == 4.0
