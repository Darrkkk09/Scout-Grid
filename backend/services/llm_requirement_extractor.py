import json
import logging
import os
import socket
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Set, Tuple

from models.search import ParsedRequirements
from services.requirement_validator import RequirementValidator

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert recruitment natural language query parser for ScoutGrid.
Your ONLY job is to convert recruiter search queries into structured candidate-search requirements.

Extract the following fields strictly according to this JSON schema:
{
  "role": string or null (e.g. "backend engineer", "software engineer"),
  "skills": list of strings (e.g. ["Python", "FastAPI"]),
  "location": string or null (e.g. "Bangalore", "Hyderabad"),
  "min_experience": number or null (e.g. 3.0),
  "max_experience": number or null (e.g. 5.0),
  "semantic_query": string or null (semantic intent or domain details not covered by exact skills/role)
}

RULES:
1. Never invent requirements not stated or strongly implied by the query.
2. Only return valid JSON. No explanations, markdown fences, or extra text.
3. Normalize skill names to canonical forms (e.g., "Python", "React", "AWS", "Kubernetes").
4. If experience is stated as "3+ years", set min_experience=3.0 and max_experience=null.
5. Keep non-exact skill semantic concepts (e.g., "built scalable APIs and distributed systems") in semantic_query.
"""

RETRYABLE_HTTP_CODES = {429, 500, 502, 503, 504}
NON_RETRYABLE_HTTP_CODES = {400, 404, 422}
AUTH_HTTP_CODES = {401, 403}

# Global in-process key cooldown registry (key -> cooldown expiration timestamp)
KEY_COOLDOWN_REGISTRY: Dict[str, float] = {}


class LLMRequirementExtractor:
    """
    Robust, bounded, and configurable Gemini & OpenAI requirement extraction service.
    Supports multi-key rotation, multi-model fallback, per-request & total time budgets,
    retry classification, and in-memory key cooldowns.
    """

    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "gemini").lower()

        # Models configuration (default: stable 2.5 models)
        models_str = os.getenv(
            "LLM_MODELS",
            os.getenv("LLM_MODEL", "gemini-2.5-flash-lite,gemini-2.5-flash"),
        )
        self.models: List[str] = [m.strip() for m in models_str.split(",") if m.strip()]

        # Limits & Time Budget Configuration
        self.timeout_seconds = float(os.getenv("LLM_TIMEOUT_SECONDS", "2.5"))
        self.total_timeout_seconds = float(os.getenv("LLM_TOTAL_TIMEOUT_SECONDS", "6.0"))
        self.max_attempts = int(os.getenv("LLM_MAX_ATTEMPTS", "3"))

        # Retry Backoff Delays (ms)
        self.retry_base_delay_ms = float(os.getenv("LLM_RETRY_BASE_DELAY_MS", "100"))
        self.retry_max_delay_ms = float(os.getenv("LLM_RETRY_MAX_DELAY_MS", "500"))

        # Key Cooldown (seconds)
        self.key_cooldown_seconds = float(os.getenv("LLM_KEY_COOLDOWN_SECONDS", "30"))

        # Load API keys (precedence: GEMINI_API_KEY_1..5 > GEMINI_API_KEYS / GEMINI_API_KEY)
        self.api_keys: List[str] = self._load_api_keys()
        self._key_index = 0

    def _load_api_keys(self) -> List[str]:
        keys: List[str] = []

        # 1. Explicit indexed keys (Highest Precedence)
        for i in range(1, 6):
            key = os.getenv(f"GEMINI_API_KEY_{i}") or os.getenv(f"LLM_API_KEY_{i}")
            if key and key.strip() and key.strip() not in keys:
                keys.append(key.strip())

        # 2. Comma-separated or single primary key (Secondary Precedence)
        primary = os.getenv(
            "GEMINI_API_KEYS",
            os.getenv("GEMINI_API_KEY", os.getenv("LLM_API_KEYS", os.getenv("LLM_API_KEY", ""))),
        ).strip()
        if primary:
            for k in primary.split(","):
                if k.strip() and k.strip() not in keys:
                    keys.append(k.strip())

        return keys[:5]

    def is_configured(self) -> bool:
        return len(self.api_keys) > 0

    def _get_available_key(self, used_in_request: Set[str]) -> Optional[Tuple[str, int]]:
        """Returns (key, index) for the next key not on cooldown and not already failed in this request."""
        if not self.api_keys:
            return None

        now = time.time()
        num_keys = len(self.api_keys)

        for _ in range(num_keys):
            idx = self._key_index % num_keys
            key = self.api_keys[idx]
            self._key_index += 1

            # Check if key is on cooldown
            cooldown_until = KEY_COOLDOWN_REGISTRY.get(key, 0.0)
            if now < cooldown_until:
                continue

            if key not in used_in_request:
                return key, idx

        # Fallback: if all available keys were tried in this request, pick any non-cooldown key
        for idx, key in enumerate(self.api_keys):
            if now >= KEY_COOLDOWN_REGISTRY.get(key, 0.0):
                return key, idx

        return None

    def _mark_key_cooldown(self, key: str):
        if key:
            KEY_COOLDOWN_REGISTRY[key] = time.time() + self.key_cooldown_seconds
            logger.warning(
                "Marked API key index on cooldown for %s seconds due to auth/quota error",
                self.key_cooldown_seconds,
            )

    def extract_requirements(
        self, query: str
    ) -> Tuple[Optional[ParsedRequirements], Optional[str]]:
        """
        Attempts requirements extraction bounded by max_attempts and total_timeout_seconds budget.
        Returns tuple of (ParsedRequirements | None, error_reason | None).
        """
        if not self.is_configured():
            return None, "llm_not_configured"

        if not query or not query.strip():
            return None, "empty_query"

        start_time = time.time()
        used_keys_in_request: Set[str] = set()
        last_error = "llm_api_error"
        attempt_count = 0

        model_idx = 0

        while attempt_count < self.max_attempts:
            # Check remaining total budget
            elapsed_total = time.time() - start_time
            remaining_budget = self.total_timeout_seconds - elapsed_total
            if remaining_budget <= 0.1:  # Not enough budget for attempt
                logger.warning("LLM total time budget exhausted (%ss)", self.total_timeout_seconds)
                last_error = "llm_total_timeout"
                break

            key_tuple = self._get_available_key(used_keys_in_request)
            if not key_tuple:
                logger.warning("No available LLM API keys (all keys on cooldown or exhausted)")
                last_error = "no_available_keys"
                break

            current_key, key_idx = key_tuple
            current_model = self.models[model_idx % len(self.models)]
            attempt_count += 1

            # Determine request timeout constrained by total budget
            per_request_timeout = min(self.timeout_seconds, remaining_budget)

            t0 = time.time()
            try:
                if "gemini" in self.provider or "gemini" in current_model.lower():
                    raw_response = self._call_gemini_api(
                        query, current_key, current_model, per_request_timeout
                    )
                else:
                    raw_response = self._call_openai_api(
                        query, current_key, current_model, per_request_timeout
                    )

                req_latency = round((time.time() - t0) * 1000.0, 2)

                if raw_response:
                    clean_json_str = self._clean_json_string(raw_response)
                    data = json.loads(clean_json_str)
                    validated_reqs = RequirementValidator.validate_and_convert(data)

                    if validated_reqs:
                        logger.info(
                            "requirement_extraction source=llm model=%s attempts=%s latency_ms=%s",
                            current_model,
                            attempt_count,
                            req_latency,
                        )
                        return validated_reqs, None

                    last_error = "schema_validation_failed"
                    # Schema validation failure is non-retryable for same payload
                    break

            except (TimeoutError, socket.timeout):
                logger.warning(
                    "LLM timeout attempt %s/%s model=%s key_idx=%s",
                    attempt_count,
                    self.max_attempts,
                    current_model,
                    key_idx,
                )
                used_keys_in_request.add(current_key)
                last_error = "llm_timeout"

            except urllib.error.HTTPError as http_err:
                code = http_err.code
                logger.warning(
                    "LLM HTTP %s error attempt %s/%s model=%s key_idx=%s",
                    code,
                    attempt_count,
                    self.max_attempts,
                    current_model,
                    key_idx,
                )

                if code in AUTH_HTTP_CODES:
                    self._mark_key_cooldown(current_key)
                    used_keys_in_request.add(current_key)
                    last_error = f"http_{code}_auth"
                elif code in RETRYABLE_HTTP_CODES:
                    used_keys_in_request.add(current_key)
                    last_error = f"http_{code}_retryable"
                elif code in NON_RETRYABLE_HTTP_CODES:
                    last_error = f"http_{code}_non_retryable"
                    break  # Do not waste retries on 400 bad request
                else:
                    last_error = f"http_{code}"

            except json.JSONDecodeError:
                logger.warning("Invalid JSON output attempt %s/%s model=%s", attempt_count, self.max_attempts, current_model)
                last_error = "invalid_json"
                # Do not retry malformed json repeatedly on same prompt
                break
            except Exception as e:
                logger.warning("LLM exception attempt %s/%s: %s", attempt_count, self.max_attempts, str(e))
                last_error = f"llm_api_error: {str(e)}"
                used_keys_in_request.add(current_key)

            # Rotate model for next attempt if current model failed repeatedly
            model_idx += 1

            # Bounded exponential backoff delay before next attempt if budget permits
            if attempt_count < self.max_attempts:
                delay_sec = min(
                    (self.retry_base_delay_ms * (2 ** (attempt_count - 1))) / 1000.0,
                    self.retry_max_delay_ms / 1000.0,
                )
                remaining_after_delay = self.total_timeout_seconds - (time.time() - start_time)
                if remaining_after_delay > delay_sec:
                    time.sleep(delay_sec)

        return None, last_error

    def _call_gemini_api(
        self, query: str, api_key: str, model: str, timeout: float
    ) -> Optional[str]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {"parts": [{"text": f"{SYSTEM_PROMPT}\n\nRecruiter Query: {query}"}]}
            ],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.0,
            },
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                res_body = json.loads(resp.read().decode("utf-8"))
                candidates = res_body.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
        return None

    def _call_openai_api(
        self, query: str, api_key: str, model: str, timeout: float
    ) -> Optional[str]:
        base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1/chat/completions")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0,
        }

        req = urllib.request.Request(
            base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                res_body = json.loads(resp.read().decode("utf-8"))
                choices = res_body.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
        return None

    @staticmethod
    def _clean_json_string(text: str) -> str:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()
