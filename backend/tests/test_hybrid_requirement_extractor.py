import json
import urllib.error
import urllib.request
from unittest.mock import MagicMock, patch
import pytest

from app.models.search import ParsedRequirements
from app.services.hybrid_requirement_extractor import HybridRequirementExtractor
from app.services.llm_requirement_extractor import LLMRequirementExtractor
from app.services.requirement_validator import RequirementValidator


# 1. Validator Tests
def test_validator_valid_json():
    data = {
        "role": "backend engineer",
        "skills": ["Python", "FastAPI"],
        "location": "Bangalore",
        "min_experience": 3.0,
        "max_experience": 5.0,
        "semantic_query": "built microservices",
    }
    reqs = RequirementValidator.validate_and_convert(data)
    assert reqs is not None
    assert reqs.job_title == "backend engineer"
    assert reqs.skills == ["Python", "FastAPI"]
    assert reqs.location == "Bangalore"
    assert reqs.min_experience == 3.0
    assert reqs.max_experience == 5.0
    assert reqs.semantic_query == "built microservices"


def test_validator_swapped_experience_correction():
    data = {
        "role": "engineer",
        "min_experience": 5.0,
        "max_experience": 2.0,
    }
    reqs = RequirementValidator.validate_and_convert(data)
    assert reqs is not None
    assert reqs.min_experience == 2.0
    assert reqs.max_experience == 5.0


def test_validator_invalid_types():
    assert RequirementValidator.validate_and_convert(None) is None
    assert RequirementValidator.validate_and_convert("not a dict") is None


# 2. LLM Requirement Extractor Success & Failure Scenarios
@patch("urllib.request.urlopen")
def test_llm_extractor_success_gemini(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps({
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps({
                                "role": "software engineer",
                                "skills": ["Python"],
                                "location": "Hyderabad",
                                "min_experience": 4.0,
                                "max_experience": None,
                                "semantic_query": None
                            })
                        }
                    ]
                }
            }
        ]
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    extractor = LLMRequirementExtractor()
    extractor.api_keys = ["AIzaSyTestKey1", "AIzaSyTestKey2"]
    extractor.models = ["gemini-1.5-flash", "gemini-2.0-flash"]

    reqs, error = extractor.extract_requirements("Python engineer in Hyderabad with 4+ years")
    assert error is None
    assert reqs is not None
    assert reqs.skills == ["Python"]
    assert reqs.location == "Hyderabad"
    assert reqs.min_experience == 4.0


@patch("urllib.request.urlopen")
def test_llm_extractor_invalid_json_fallback(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps({
        "candidates": [
            {"content": {"parts": [{"text": "INVALID JSON OUTPUT"}]}}
        ]
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    extractor = LLMRequirementExtractor()
    extractor.api_keys = ["AIzaSyTestKey1"]

    reqs, error = extractor.extract_requirements("Python developer")
    assert reqs is None
    assert error == "invalid_json"


def test_llm_extractor_multi_key_loading():
    with patch.dict("os.environ", {
        "LLM_PROVIDER": "gemini",
        "LLM_MODELS": "gemini-1.5-flash,gemini-2.0-flash,gemini-1.5-pro",
        "GEMINI_API_KEY_1": "key1",
        "GEMINI_API_KEY_2": "key2",
        "GEMINI_API_KEY_3": "key3",
        "GEMINI_API_KEY_4": "key4",
        "GEMINI_API_KEY_5": "key5",
    }):
        extractor = LLMRequirementExtractor()
        assert len(extractor.api_keys) == 5
        assert extractor.api_keys == ["key1", "key2", "key3", "key4", "key5"]
        assert len(extractor.models) == 3
        assert extractor.models == ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]


def test_llm_extractor_unconfigured_fallback():
    extractor = LLMRequirementExtractor()
    extractor.api_keys = []  # Unconfigured
    reqs, error = extractor.extract_requirements("Python developer")
    assert reqs is None
    assert error == "llm_not_configured"


def test_llm_extractor_max_attempts_budget():
    extractor = LLMRequirementExtractor()
    extractor.api_keys = ["key1", "key2", "key3"]
    extractor.max_attempts = 2  # Enforce max 2 attempts

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = TimeoutError("Timed out")
        reqs, error = extractor.extract_requirements("Python developer")
        assert reqs is None
        assert error == "llm_timeout"
        # Should attempt at most 2 times, not 3 or more
        assert mock_urlopen.call_count == 2


@patch("urllib.request.urlopen")
def test_llm_extractor_retry_on_429_success_on_key2(mock_urlopen):
    # Setup HTTP 429 Error on first attempt, 200 OK on second attempt
    err_429 = urllib.error.HTTPError(
        url="http://test", code=429, msg="Too Many Requests", hdrs={}, fp=None
    )
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps({
        "candidates": [
            {"content": {"parts": [{"text": json.dumps({"role": "engineer", "skills": ["Go"]})}]}}
        ]
    }).encode("utf-8")
    mock_ctx = MagicMock()
    mock_ctx.__enter__.return_value = mock_resp

    mock_urlopen.side_effect = [err_429, mock_ctx]

    extractor = LLMRequirementExtractor()
    extractor.api_keys = ["key1", "key2"]
    extractor.retry_base_delay_ms = 1.0  # Speed up test

    reqs, error = extractor.extract_requirements("Go engineer")
    assert error is None
    assert reqs is not None
    assert reqs.skills == ["Go"]
    assert mock_urlopen.call_count == 2


@patch("urllib.request.urlopen")
def test_llm_extractor_non_retryable_400_bad_request(mock_urlopen):
    err_400 = urllib.error.HTTPError(
        url="http://test", code=400, msg="Bad Request", hdrs={}, fp=None
    )
    mock_urlopen.side_effect = err_400

    extractor = LLMRequirementExtractor()
    extractor.api_keys = ["key1", "key2", "key3"]
    extractor.max_attempts = 3

    reqs, error = extractor.extract_requirements("Python developer")
    assert reqs is None
    assert "400" in error
    # Non-retryable error should immediately break without exhausting remaining attempts
    assert mock_urlopen.call_count == 1


# 3. Hybrid Orchestrator Tests
def test_hybrid_fallback_to_rule_based():
    mock_llm = MagicMock()
    mock_llm.is_configured.return_value = True
    mock_llm.extract_requirements.return_value = (None, "llm_timeout")

    hybrid = HybridRequirementExtractor(llm_extractor=mock_llm)
    reqs, source, reason = hybrid.extract_with_metadata("Python backend engineers with 3+ years in Bangalore")

    assert source == "fallback"
    assert reason == "llm_timeout"
    assert "Python" in reqs.skills
    assert reqs.location == "Bangalore"
    assert reqs.min_experience == 3.0


def test_hybrid_llm_success():
    mock_llm = MagicMock()
    mock_llm.is_configured.return_value = True
    llm_parsed = ParsedRequirements(
        skills=["Python", "FastAPI"],
        location="Bangalore",
        min_experience=3.0,
        job_title="backend engineer",
        semantic_query="high throughput APIs",
    )
    mock_llm.extract_requirements.return_value = (llm_parsed, None)

    hybrid = HybridRequirementExtractor(llm_extractor=mock_llm)
    reqs, source, reason = hybrid.extract_with_metadata("Python backend engineers with 3+ years in Bangalore")

    assert source == "llm"
    assert reason is None
    assert reqs.skills == ["Python", "FastAPI"]
    assert reqs.semantic_query == "high throughput APIs"

