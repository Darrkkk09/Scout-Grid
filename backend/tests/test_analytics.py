import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_get_dashboard_analytics(monkeypatch):
    async def mock_count_documents(self, filter_doc):
        return 100000

    from motor.motor_asyncio import AsyncIOMotorCollection
    monkeypatch.setattr(AsyncIOMotorCollection, "count_documents", mock_count_documents)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/analytics/dashboard")

    assert response.status_code == 200
    data = response.json()
    assert "total_candidates" in data
    assert data["total_candidates"] == 100000
