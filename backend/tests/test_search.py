import os
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")
os.environ["MONGODB_DATABASE"] = "scoutgrid_test"
os.environ["GEMINI_API_KEY_1"] = ""
os.environ["GEMINI_API_KEY_2"] = ""
os.environ["GEMINI_API_KEY_3"] = ""
os.environ["GEMINI_API_KEY_4"] = ""
os.environ["GEMINI_API_KEY_5"] = ""
os.environ["GEMINI_API_KEYS"] = ""
os.environ["GEMINI_API_KEY"] = ""
os.environ["LLM_API_KEY"] = ""

from app.database import get_db
from app.main import app
from app.services.requirement_extractor import RequirementExtractor
from app.services.search_service import SearchService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(autouse=True)
async def clean_db(client):
    db = get_db()
    await db["candidates"].drop()
    yield
    await db["candidates"].drop()


# ---------------------------------------------------------------------------
# RequirementExtractor Unit Tests
# ---------------------------------------------------------------------------

def test_extraction_skills():
    reqs = RequirementExtractor.extract("Python and FastAPI developers")
    assert "Python" in reqs.skills
    assert "FastAPI" in reqs.skills


def test_extraction_location():
    reqs = RequirementExtractor.extract("React developers in Bangalore")
    assert reqs.location == "Bangalore"


def test_extraction_experience_plus():
    reqs = RequirementExtractor.extract("Python backend engineers with 3+ years of experience in Bangalore")
    assert "Python" in reqs.skills
    assert reqs.location == "Bangalore"
    assert reqs.min_experience == 3.0
    assert reqs.job_title == "backend engineer"


def test_extraction_experience_less():
    reqs = RequirementExtractor.extract("Java developers with less than 5 years")
    assert "Java" in reqs.skills
    assert reqs.max_experience == 5.0


def test_extraction_multiple_skills_location_exp():
    reqs = RequirementExtractor.extract("Senior Python FastAPI developers with 5 years experience in Hyderabad")
    assert set(reqs.skills) == {"Python", "FastAPI"}
    assert reqs.location == "Hyderabad"
    assert reqs.min_experience == 5.0
    assert reqs.job_title == "developer"


def test_extraction_empty_query():
    reqs = RequirementExtractor.extract("")
    assert reqs.skills == []
    assert reqs.location is None
    assert reqs.min_experience is None


# ---------------------------------------------------------------------------
# SearchService Mongo Query Construction Unit Tests
# ---------------------------------------------------------------------------

def test_mongo_query_construction():
    reqs = RequirementExtractor.extract("Python FastAPI developers with 3+ years in Bangalore")
    service = SearchService(collection=None)
    query_dict = service.build_mongo_query(reqs)

    assert set(query_dict["skills"]["$all"]) == {"Python", "FastAPI"}
    assert "$regex" in query_dict["location"]
    assert query_dict["experience_years"] == {"$gte": 3.0}
    assert "$or" in query_dict


# ---------------------------------------------------------------------------
# Search API Integration Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_search_api_endpoint(client: AsyncClient):
    db = get_db()
    await db["candidates"].insert_many([
        {
            "name": "Aarav Sharma",
            "email": "aarav@example.com",
            "location": "Bangalore",
            "experience_years": 4.5,
            "skills": ["Python", "FastAPI", "MongoDB"],
            "education": "B.Tech Computer Science",
            "experience": [
                {
                    "company": "Tech Corp",
                    "title": "Backend Engineer",
                    "start_date": "2020-01-01",
                    "end_date": None,
                    "description": "Building APIs",
                }
            ],
        },
        {
            "name": "Priya Patel",
            "email": "priya@example.com",
            "location": "Hyderabad",
            "experience_years": 2.0,
            "skills": ["React", "JavaScript", "Node.js"],
            "education": "BCA",
            "experience": [
                {
                    "company": "Web Solutions",
                    "title": "Frontend Developer",
                    "start_date": "2022-01-01",
                    "end_date": None,
                    "description": "React web app development",
                }
            ],
        },

    ])

    # Test 1: Python query matching Aarav
    res1 = await client.post("/search", json={
        "query": "Python backend engineers with 3+ years in Bangalore"
    })
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["total"] == 1
    assert data1["results"][0]["name"] == "Aarav Sharma"
    assert "Python" in data1["parsed_requirements"]["skills"]
    assert data1["parsed_requirements"]["location"] == "Bangalore"
    assert data1["parsed_requirements"]["min_experience"] == 3.0

    # Test 2: React query matching Priya
    res2 = await client.post("/search", json={
        "query": "React developers in Hyderabad"
    })
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["total"] == 1
    assert data2["results"][0]["name"] == "Priya Patel"

    # Test 3: Query with no matching candidates
    res3 = await client.post("/search", json={
        "query": "C++ engineers in Delhi with 10+ years"
    })
    assert res3.status_code == 200
    data3 = res3.json()
    assert data3["total"] == 0
    assert data3["results"] == []

    # Test 4: Offset Pagination
    res4 = await client.post("/search?page=1&limit=1", json={
        "query": "developer"
    })
    assert res4.status_code == 200
    data4 = res4.json()
    assert data4["limit"] == 1
    assert len(data4["results"]) == 1


# ---------------------------------------------------------------------------
# Cursor Pagination Unit & API Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cursor_pagination_flow(client: AsyncClient):
    db = get_db()
    # Insert 3 candidates
    candidates_data = [
        {
            "name": f"Candidate {i}",
            "email": f"cand{i}@example.com",
            "location": "Bangalore",
            "experience_years": 3.0,
            "skills": ["Python"],
            "education": "B.Tech",
            "experience": [{"company": "Co", "title": "Developer", "start_date": "2020-01-01"}],
        }
        for i in range(1, 4)
    ]
    await db["candidates"].insert_many(candidates_data)

    # Page 1 in cursor mode (limit=1)
    res1 = await client.post("/search", json={
        "query": "Python developers",
        "limit": 1,
        "pagination_mode": "cursor"
    })
    assert res1.status_code == 200
    d1 = res1.json()
    assert d1["pagination_mode"] == "cursor"
    assert d1["total"] is None  # Exact count avoided!
    assert len(d1["results"]) == 1
    assert d1["has_next_page"] is True
    assert d1["next_cursor"] is not None

    cursor1 = d1["next_cursor"]

    # Page 2 using cursor1
    res2 = await client.post("/search", json={
        "query": "Python developers",
        "limit": 1,
        "pagination_mode": "cursor",
        "cursor": cursor1
    })
    assert res2.status_code == 200
    d2 = res2.json()
    assert len(d2["results"]) == 1
    assert d2["results"][0]["id"] != d1["results"][0]["id"]
    assert d2["has_next_page"] is True
    assert d2["next_cursor"] is not None

    cursor2 = d2["next_cursor"]

    # Page 3 using cursor2
    res3 = await client.post("/search", json={
        "query": "Python developers",
        "limit": 1,
        "pagination_mode": "cursor",
        "cursor": cursor2
    })
    assert res3.status_code == 200
    d3 = res3.json()
    assert len(d3["results"]) == 1
    assert d3["results"][0]["id"] != d2["results"][0]["id"]
    assert d3["has_next_page"] is False
    assert d3["next_cursor"] is None


@pytest.mark.asyncio
async def test_cursor_invalid_token(client: AsyncClient):
    res = await client.post("/search", json={
        "query": "Python developers",
        "pagination_mode": "cursor",
        "cursor": "invalid_base64_not_json!!!"
    })
    assert res.status_code == 400
    assert "Invalid pagination cursor" in res.json()["detail"]


@pytest.mark.asyncio
async def test_cursor_mode_does_not_call_count_documents(monkeypatch):
    class MockCollection:
        def __init__(self):
            self.count_called = False

        async def count_documents(self, filter_dict):
            self.count_called = True
            return 9999

        def find(self, filter_dict):
            class MockCursor:
                def sort(self, key, direction):
                    return self
                def limit(self, limit_val):
                    return self
                async def to_list(self, length):
                    return []
            return MockCursor()

    mock_col = MockCollection()
    service = SearchService(mock_col)

    response = await service.search(
        query="Python developers",
        limit=20,
        pagination_mode="cursor"
    )

    assert mock_col.count_called is False
    assert response.has_next_page is False
    assert response.total is None


