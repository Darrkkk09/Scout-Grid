"""
API tests for the ScoutGrid Candidate Service.

Run with:
    pytest tests/ -v

Requires a running MongoDB instance (uses a separate test database).
Set MONGODB_DATABASE=scoutgrid_test to isolate test data.
"""

import os
import pytest
import pytest_asyncio

os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")
os.environ.setdefault("MONGODB_DATABASE", "scoutgrid_test")

from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import get_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(autouse=True)
async def clean_db(client):
    """Drop test collection before and after each test."""
    db = get_db()
    await db["candidates"].drop()
    yield
    await db["candidates"].drop()


SAMPLE_CANDIDATE = {
    "name": "Test User",
    "email": "test.user@example.com",
    "location": "Bangalore",
    "experience_years": 4.5,
    "skills": ["Python", "FastAPI", "MongoDB"],
    "education": "B.Tech Computer Science",
    "experience": [
        {
            "company": "Acme Corp",
            "title": "Backend Engineer",
            "start_date": "2021-06-01",
            "end_date": "2023-12-31",
            "description": "Built REST APIs with FastAPI.",
        }
    ],
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "ScoutGrid Candidate Service"


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_create_candidate(client: AsyncClient):
    response = await client.post("/candidates", json=SAMPLE_CANDIDATE)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert isinstance(data["id"], str)


@pytest.mark.asyncio
async def test_get_candidate(client: AsyncClient):
    # Create first
    res = await client.post("/candidates", json=SAMPLE_CANDIDATE)
    cid = res.json()["id"]

    response = await client.get(f"/candidates/{cid}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == cid
    assert data["name"] == "Test User"
    assert data["email"] == "test.user@example.com"
    assert data["skills"] == ["Python", "FastAPI", "MongoDB"]
    assert len(data["experience"]) == 1


@pytest.mark.asyncio
async def test_get_candidate_not_found(client: AsyncClient):
    fake_id = "507f1f77bcf86cd799439011"
    response = await client.get(f"/candidates/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_candidate_invalid_id(client: AsyncClient):
    response = await client.get("/candidates/not-an-object-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_candidates_pagination(client: AsyncClient):
    # Create a candidate so the list is non-empty
    await client.post("/candidates", json=SAMPLE_CANDIDATE)

    response = await client.get("/candidates?page=1&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "page" in data
    assert "candidates" in data
    assert data["page"] == 1
    assert isinstance(data["candidates"], list)
    assert len(data["candidates"]) > 0


@pytest.mark.asyncio
async def test_filter_by_skill(client: AsyncClient):
    await client.post("/candidates", json=SAMPLE_CANDIDATE)
    response = await client.get("/candidates?skill=Python")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    for c in data["candidates"]:
        assert "Python" in c["skills"]


@pytest.mark.asyncio
async def test_filter_by_location(client: AsyncClient):
    await client.post("/candidates", json=SAMPLE_CANDIDATE)
    response = await client.get("/candidates?location=bangalore")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    for c in data["candidates"]:
        assert "bangalore" in c["location"].lower()


@pytest.mark.asyncio
async def test_filter_combined(client: AsyncClient):
    await client.post("/candidates", json=SAMPLE_CANDIDATE)
    response = await client.get("/candidates?skill=Python&location=Bangalore&min_experience=2")
    assert response.status_code == 200
    data = response.json()
    for c in data["candidates"]:
        assert "Python" in c["skills"]
        assert c["experience_years"] >= 2.0


@pytest.mark.asyncio
async def test_create_candidate_missing_field(client: AsyncClient):
    invalid = {"name": "No Email"}
    response = await client.post("/candidates", json=invalid)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_candidate_invalid_email(client: AsyncClient):
    invalid = {**SAMPLE_CANDIDATE, "email": "not-an-email"}
    response = await client.post("/candidates", json=invalid)
    assert response.status_code == 422
