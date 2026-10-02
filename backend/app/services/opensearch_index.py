import logging
from typing import Any, Dict
from opensearchpy import OpenSearch
from app.services.opensearch_client import get_opensearch_client

logger = logging.getLogger(__name__)

CANDIDATES_INDEX_NAME = "candidates"

CANDIDATE_INDEX_MAPPING: Dict[str, Any] = {
    "settings": {
        "index": {
            "number_of_shards": 1,
            "number_of_replicas": 1,
        }
    },
    "mappings": {
        "properties": {
            "candidate_id": {"type": "keyword"},
            "name": {"type": "text"},
            "email": {"type": "keyword"},
            "location": {"type": "keyword"},
            "experience_years": {"type": "float"},
            "skills": {"type": "keyword"},
            "education": {"type": "text"},
            "experience": {
                "type": "nested",
                "properties": {
                    "company": {"type": "text"},
                    "title": {"type": "text"},
                    "start_date": {"type": "keyword"},
                    "end_date": {"type": "keyword"},
                    "description": {"type": "text"},
                },
            },
        }
    },
}


def candidate_to_search_document(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms a raw MongoDB candidate dictionary or Candidate model dict into
    an OpenSearch indexable document.
    Ensures _id is serialized to candidate_id string.
    """
    doc = dict(candidate)
    
    # Extract & convert _id to string candidate_id
    if "_id" in doc:
        raw_id = doc.pop("_id")
        doc["candidate_id"] = str(raw_id)
    elif "id" in doc:
        doc["candidate_id"] = str(doc.pop("id"))

    # Convert numeric experience_years to float safely
    try:
        doc["experience_years"] = float(doc.get("experience_years", 0.0))
    except (ValueError, TypeError):
        doc["experience_years"] = 0.0

    # Ensure skills is a list of strings
    skills_raw = doc.get("skills", [])
    if isinstance(skills_raw, list):
        doc["skills"] = [str(s) for s in skills_raw]
    elif isinstance(skills_raw, str):
        doc["skills"] = [s.strip() for s in skills_raw.split(",") if s.strip()]
    else:
        doc["skills"] = []

    # Format experience items
    exp_raw = doc.get("experience", [])
    cleaned_experience = []
    if isinstance(exp_raw, list):
        for item in exp_raw:
            if isinstance(item, dict):
                cleaned_experience.append({
                    "company": str(item.get("company", "")),
                    "title": str(item.get("title", "")),
                    "start_date": str(item.get("start_date")) if item.get("start_date") else None,
                    "end_date": str(item.get("end_date")) if item.get("end_date") else None,
                    "description": str(item.get("description")) if item.get("description") else None,
                })
    doc["experience"] = cleaned_experience

    doc["name"] = str(doc.get("name", ""))
    doc["email"] = str(doc.get("email", ""))
    doc["location"] = str(doc.get("location", ""))
    doc["education"] = str(doc.get("education", ""))

    return doc


def check_index_exists(client: OpenSearch, index_name: str = CANDIDATES_INDEX_NAME) -> bool:
    """Checks if the specified OpenSearch index exists."""
    return bool(client.indices.exists(index=index_name))


def create_candidate_index(client: OpenSearch, index_name: str = CANDIDATES_INDEX_NAME) -> bool:
    """
    Safely creates the candidate OpenSearch index with mapping if it does not already exist.
    Returns True if created, False if it already existed.
    """
    if check_index_exists(client, index_name):
        logger.info("OpenSearch index '%s' already exists.", index_name)
        return False

    client.indices.create(index=index_name, body=CANDIDATE_INDEX_MAPPING)
    logger.info("OpenSearch index '%s' created successfully.", index_name)
    return True
