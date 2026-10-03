import pytest
from app.services.embedding_service import EmbeddingService, candidate_to_semantic_text
from app.services.opensearch_search_service import reciprocal_rank_fusion


# 1. Semantic Text Generation Test
def test_candidate_to_semantic_text():
    cand = {
        "candidate_id": "12345",
        "name": "Jane Doe",
        "email": "jane@example.com",  # Should be excluded
        "skills": ["Python", "FastAPI"],
        "education": "B.Tech Computer Science",
        "experience": [
            {
                "title": "Backend Engineer",
                "company": "Tech Corp",
                "description": "Built distributed microservices",
            }
        ],
    }

    text = candidate_to_semantic_text(cand)

    assert "jane@example.com" not in text
    assert "12345" not in text
    assert "Skills: Python, FastAPI" in text
    assert "Experience:\nBackend Engineer at Tech Corp\nBuilt distributed microservices" in text
    assert "Education: B.Tech Computer Science" in text


# 2. Embedding Service Test
def test_embedding_service_dimension_and_fallback():
    svc = EmbeddingService()
    vec = svc.embed_text("Senior Python Developer")

    assert isinstance(vec, list)
    assert len(vec) == svc.dimension
    assert all(isinstance(v, float) for v in vec)


# 3. Reciprocal Rank Fusion (RRF) Deduplication & Scoring Test
def test_reciprocal_rank_fusion():
    bm25_hits = [
        {"_id": "cand_1", "_source": {"candidate_id": "cand_1", "name": "Cand 1"}},
        {"_id": "cand_2", "_source": {"candidate_id": "cand_2", "name": "Cand 2"}},
    ]
    vector_hits = [
        {"_id": "cand_2", "_source": {"candidate_id": "cand_2", "name": "Cand 2"}},
        {"_id": "cand_3", "_source": {"candidate_id": "cand_3", "name": "Cand 3"}},
    ]

    fused = reciprocal_rank_fusion(bm25_hits, vector_hits, rrf_k=60, top_k=10)

    # Cand 2 appears in both lists (rank 2 in BM25, rank 1 in Vector) -> should have highest score
    assert len(fused) == 3
    assert fused[0]["_source"]["candidate_id"] == "cand_2"
    assert "_rrf_score" in fused[0]
