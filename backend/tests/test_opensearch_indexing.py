import pytest
from unittest.mock import MagicMock, patch
from bson import ObjectId

from app.services.opensearch_index import (
    CANDIDATE_INDEX_MAPPING,
    CANDIDATES_INDEX_NAME,
    candidate_to_search_document,
    check_index_exists,
    create_candidate_index,
)
from scripts.index_candidates import bulk_index_candidates


# 1. Mapping Verification Test
def test_candidate_index_mapping_structure():
    """Verify that CANDIDATE_INDEX_MAPPING contains expected property types."""
    props = CANDIDATE_INDEX_MAPPING["mappings"]["properties"]

    assert props["candidate_id"]["type"] == "keyword"
    assert props["name"]["type"] == "text"
    assert props["email"]["type"] == "keyword"
    assert props["location"]["type"] == "keyword"
    assert props["experience_years"]["type"] == "float"
    assert props["skills"]["type"] == "keyword"
    assert props["education"]["type"] == "text"
    assert props["experience"]["type"] == "nested"
    assert props["experience"]["properties"]["title"]["type"] == "text"
    assert props["experience"]["properties"]["company"]["type"] == "text"


# 2. Document Transformation Test
def test_candidate_to_search_document_transformation():
    """Verify raw MongoDB candidate document is converted into OpenSearch search document."""
    sample_mongo_candidate = {
        "_id": ObjectId("64f3a1b2c9e77f001234abcd"),
        "name": "Ananya Sharma",
        "email": "ananya@example.com",
        "location": "Bangalore",
        "experience_years": 4.5,
        "skills": ["Python", "FastAPI", "PostgreSQL"],
        "education": "M.Tech CS",
        "experience": [
            {
                "company": "Tech Corp",
                "title": "Senior Backend Developer",
                "start_date": "2021-01-01",
                "end_date": "2023-12-31",
                "description": "Developed Microservices",
            }
        ],
    }

    doc = candidate_to_search_document(sample_mongo_candidate)

    assert doc["candidate_id"] == "64f3a1b2c9e77f001234abcd"
    assert "_id" not in doc
    assert doc["name"] == "Ananya Sharma"
    assert doc["email"] == "ananya@example.com"
    assert doc["location"] == "Bangalore"
    assert doc["experience_years"] == 4.5
    assert doc["skills"] == ["Python", "FastAPI", "PostgreSQL"]
    assert doc["education"] == "M.Tech CS"
    assert len(doc["experience"]) == 1
    assert doc["experience"][0]["title"] == "Senior Backend Developer"


# 3. Safe Index Creation Unit Test with Mocks
def test_create_candidate_index_creation_flow():
    """Verify create_candidate_index checks existence and calls indices.create only when missing."""
    mock_client = MagicMock()

    # Case A: Index missing -> should create index
    mock_client.indices.exists.return_value = False
    created = create_candidate_index(mock_client, CANDIDATES_INDEX_NAME)

    assert created is True
    mock_client.indices.exists.assert_called_with(index=CANDIDATES_INDEX_NAME)
    mock_client.indices.create.assert_called_once_with(
        index=CANDIDATES_INDEX_NAME, body=CANDIDATE_INDEX_MAPPING
    )

    # Case B: Index exists -> should NOT recreate or delete
    mock_client.reset_mock()
    mock_client.indices.exists.return_value = True
    created_again = create_candidate_index(mock_client, CANDIDATES_INDEX_NAME)

    assert created_again is False
    mock_client.indices.exists.assert_called_with(index=CANDIDATES_INDEX_NAME)
    mock_client.indices.create.assert_not_called()


# 4. Bulk Indexing Unit Test with Mocks
@patch("scripts.index_candidates.MongoClient")
@patch("scripts.index_candidates.create_opensearch_client")
@patch("scripts.index_candidates.helpers.bulk")
def test_bulk_indexing_flow(mock_bulk, mock_create_os_client, mock_mongo_client):
    """Verify bulk_index_candidates reads MongoDB docs, transforms, and triggers OpenSearch bulk API."""
    # Mock MongoDB
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_mongo_client.return_value.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_collection

    sample_doc = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "name": "Test User",
        "email": "test@example.com",
        "location": "Hyderabad",
        "experience_years": 2,
        "skills": ["Java"],
        "education": "B.E.",
        "experience": [],
    }
    mock_collection.find.return_value.limit.return_value = [sample_doc]

    # Mock OpenSearch & Bulk response
    mock_os_client = MagicMock()
    mock_create_os_client.return_value = mock_os_client
    mock_bulk.return_value = (1, [])

    read, success, failed, total_time, throughput = bulk_index_candidates(limit=10)

    assert read == 1
    assert success == 1
    assert failed == 0
    mock_bulk.assert_called_once()
    actions = mock_bulk.call_args[0][1]
    assert len(actions) == 1
    assert actions[0]["_index"] == CANDIDATES_INDEX_NAME
    assert actions[0]["_id"] == "507f1f77bcf86cd799439011"
    assert actions[0]["_source"]["candidate_id"] == "507f1f77bcf86cd799439011"
