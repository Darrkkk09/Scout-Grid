import logging
import os
from typing import Any, Dict, Optional, Tuple
from opensearchpy import OpenSearch
from services.embedding_service import candidate_to_semantic_text, EmbeddingService
from services.opensearch_client import get_opensearch_client

logger = logging.getLogger(__name__)

# Configurable index version / name
CANDIDATES_INDEX_NAME = os.getenv("OPENSEARCH_INDEX_NAME", "candidates")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "384"))

CANDIDATE_INDEX_MAPPING: Dict[str, Any] = {
    "settings": {
        "index": {
            "number_of_shards": 1,
            "number_of_replicas": 1,
            "knn": True,  # Enable k-NN plugin for vector search
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
            # k-NN Vector Embedding Field Definition
            "embedding": {
                "type": "knn_vector",
                "dimension": EMBEDDING_DIMENSION,
                "method": {
                    "name": "hnsw",
                    "space_type": "cosinesimil",
                    "engine": "lucene",
                },
            },
        }
    },
}


def candidate_to_search_document(
    candidate: Dict[str, Any],
    embedding_service: Optional[EmbeddingService] = None,
    generate_embedding: bool = False,
) -> Dict[str, Any]:
    """
    Transforms a raw MongoDB candidate dictionary or Candidate model dict into
    an OpenSearch indexable document.
    Optionally computes embedding vector if generate_embedding is True and embedding is missing.
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

    # Vector embedding handling
    if "embedding" in doc and isinstance(doc["embedding"], list):
        # Already embedded
        pass
    elif generate_embedding:
        svc = embedding_service or EmbeddingService()
        sem_text = candidate_to_semantic_text(doc)
        doc["embedding"] = svc.embed_text(sem_text)

    return doc


def check_index_exists(client: OpenSearch, index_name: str = CANDIDATES_INDEX_NAME) -> bool:
    """Checks if the specified OpenSearch index exists."""
    return bool(client.indices.exists(index=index_name))


def create_candidate_index(client: OpenSearch, index_name: str = CANDIDATES_INDEX_NAME) -> bool:
    """
    Safely creates the candidate OpenSearch index with k-NN vector mapping if it does not already exist.
    Returns True if created, False if it already existed.
    """
    if check_index_exists(client, index_name):
        logger.info("OpenSearch index '%s' already exists.", index_name)
        return False

    client.indices.create(index=index_name, body=CANDIDATE_INDEX_MAPPING)
    logger.info("OpenSearch index '%s' created successfully with k-NN vector mapping.", index_name)
    return True
