"""
Unit tests for ScoutGrid Phase 3 Benchmark Utilities.

Verifies percentile calculation, query suite structure, explain stage parsing,
and requirement extraction integration without requiring a 1M document database.
"""

import os
import sys
import pytest

# Ensure scripts directory is available for import
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.benchmark_search import (
    BENCHMARK_QUERIES,
    PAGINATION_DEPTHS,
    calculate_percentiles,
    extract_stage_names,
)
from services.requirement_extractor import RequirementExtractor


def test_percentile_calculation_empty():
    res = calculate_percentiles([])
    assert res == {"min": 0.0, "avg": 0.0, "p50": 0.0, "p95": 0.0, "p99": 0.0, "max": 0.0}


def test_percentile_calculation_single_value():
    res = calculate_percentiles([42.5])
    assert res["min"] == 42.5
    assert res["avg"] == 42.5
    assert res["p50"] == 42.5
    assert res["p95"] == 42.5
    assert res["p99"] == 42.5
    assert res["max"] == 42.5


def test_percentile_calculation_known_range():
    data = [float(i) for i in range(1, 101)]  # 1 to 100
    res = calculate_percentiles(data)
    assert res["min"] == 1.0
    assert res["max"] == 100.0
    assert res["avg"] == 50.5
    assert 50.0 <= res["p50"] <= 51.0
    assert 94.0 <= res["p95"] <= 96.0
    assert 98.0 <= res["p99"] <= 100.0


def test_benchmark_query_suite_structure():
    assert len(BENCHMARK_QUERIES) == 8
    query_ids = [q["id"] for q in BENCHMARK_QUERIES]
    assert query_ids == ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8"]

    for q in BENCHMARK_QUERIES:
        assert "category" in q
        assert "query" in q
        assert isinstance(q["query"], str)
        assert len(q["query"].strip()) > 0


def test_pagination_depths_configuration():
    assert PAGINATION_DEPTHS == [1, 10, 100, 1000]


def test_extract_stage_names_nested_plan():
    mock_plan = {
        "stage": "FETCH",
        "inputStage": {
            "stage": "IXSCAN",
            "keyPattern": {"skills": 1},
        },
    }
    stages = extract_stage_names(mock_plan)
    assert stages == ["FETCH", "IXSCAN"]


def test_requirement_extraction_on_benchmark_suite():
    for q_item in BENCHMARK_QUERIES:
        parsed = RequirementExtractor.extract(q_item["query"])
        assert parsed is not None
        # Q1: "Python developers" should extract Python
        if q_item["id"] == "Q1":
            assert "Python" in parsed.skills
        # Q2: "Python developers in Bangalore" should extract Python & Bangalore
        if q_item["id"] == "Q2":
            assert "Python" in parsed.skills
            assert parsed.location == "Bangalore"
        # Q4: "Python backend engineers with 3+ years of experience" should extract min_experience=3.0
        if q_item["id"] == "Q4":
            assert parsed.min_experience == 3.0
