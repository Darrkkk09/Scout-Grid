import logging
import time
from typing import Any, Dict, Optional, Tuple

from app.models.search import ParsedRequirements
from app.services.llm_requirement_extractor import LLMRequirementExtractor
from app.services.requirement_extractor import RequirementExtractor

logger = logging.getLogger(__name__)


class HybridRequirementExtractor:
    """
    Orchestrates LLM-first requirement extraction with automatic fallback
    to deterministic rule-based RequirementExtractor.
    """

    def __init__(self, llm_extractor: Optional[LLMRequirementExtractor] = None):
        self.llm_extractor = llm_extractor or LLMRequirementExtractor()

    def extract(self, query: str) -> ParsedRequirements:
        """Simple interface returning ParsedRequirements directly."""
        reqs, _, _ = self.extract_with_metadata(query)
        return reqs

    def extract_with_metadata(
        self, query: str
    ) -> Tuple[ParsedRequirements, str, Optional[str]]:
        """
        Extracts requirements and returns (ParsedRequirements, source, fallback_reason).
        source is either 'llm' or 'fallback'.
        """
        t0 = time.perf_counter()

        if not query or not query.strip():
            return ParsedRequirements(), "fallback", "empty_query"

        # 1. Attempt LLM-first extraction if configured
        if self.llm_extractor.is_configured():
            llm_reqs, error_reason = self.llm_extractor.extract_requirements(query)
            t1 = time.perf_counter()
            elapsed_ms = round((t1 - t0) * 1000.0, 2)

            if llm_reqs is not None:
                logger.info(
                    "requirement_extraction source=llm status=success latency_ms=%s query='%s'",
                    elapsed_ms,
                    query,
                )
                return llm_reqs, "llm", None

            logger.info(
                "requirement_extraction source=fallback reason=%s latency_ms=%s query='%s'",
                error_reason,
                elapsed_ms,
                query,
            )
            fallback_reason = error_reason
        else:
            fallback_reason = "llm_not_configured"

        # 2. Fallback to deterministic rule-based extractor
        rule_reqs = RequirementExtractor.extract(query)
        t1 = time.perf_counter()
        elapsed_ms = round((t1 - t0) * 1000.0, 2)

        logger.info(
            "requirement_extraction source=fallback latency_ms=%s query='%s'",
            elapsed_ms,
            query,
        )
        return rule_reqs, "fallback", fallback_reason
