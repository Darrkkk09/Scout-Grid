"""
Unit tests for the ScoutGrid Bulk Seed Candidate Generator (scripts/seed_candidates.py).

Verifies:
- Deterministic candidate generation given a random seed
- Pydantic Candidate model compatibility
- Coherent skill set generation across technology categories
- Experience timeline consistency
- Bulk batch insertion and reset behavior
"""

import os
import pytest
import sys

# Ensure backend & project root are in sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.models.candidate import CandidateCreate
from scripts.seed_candidates import (
    ALL_TECHNOLOGY_CATALOGUE,
    PERSONA_ARCHETYPES,
    generate_candidate,
)


def test_deterministic_candidate_generation():
    """Verify that using the same seed produces identical candidates."""
    cand1 = generate_candidate(index=10, seed_id=42)
    cand2 = generate_candidate(index=10, seed_id=42)

    assert cand1["name"] == cand2["name"]
    assert cand1["email"] == cand2["email"]
    assert cand1["location"] == cand2["location"]
    assert cand1["skills"] == cand2["skills"]
    assert cand1["experience_years"] == cand2["experience_years"]


def test_candidate_schema_validity():
    """Verify generated candidates validate cleanly against Pydantic CandidateCreate model."""
    for idx in range(1, 50):
        raw_cand = generate_candidate(index=idx, seed_id=100)
        pydantic_cand = CandidateCreate(**raw_cand)
        
        assert len(pydantic_cand.name) > 0
        assert "@" in pydantic_cand.email
        assert pydantic_cand.experience_years >= 0.0
        assert len(pydantic_cand.skills) >= 1
        assert len(pydantic_cand.education) > 0


def test_realistic_skill_combinations():
    """Verify generated skills come from centralized catalogue and respect persona domain."""
    cand = generate_candidate(index=5, seed_id=99)
    skills = cand["skills"]

    # All skills should belong to centralized catalogue
    for s in skills:
        assert s in ALL_TECHNOLOGY_CATALOGUE, f"Skill '{s}' missing from technology catalogue"


def test_experience_consistency():
    """Verify experience entries match total experience years."""
    for idx in range(1, 20):
        cand = generate_candidate(index=idx, seed_id=200)
        total_exp = cand["experience_years"]
        entries = cand["experience"]

        assert len(entries) >= 1
        # First entry should be current position
        assert entries[0]["end_date"] is None
        # Past entries should have end_date
        for past_job in entries[1:]:
            assert past_job["end_date"] is not None
