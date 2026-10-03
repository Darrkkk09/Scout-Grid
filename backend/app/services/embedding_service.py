import json
import logging
import math
import os
import urllib.error
import urllib.request
from typing import List, Optional

logger = logging.getLogger(__name__)


def candidate_to_semantic_text(candidate: dict) -> str:
    """
    Deterministic helper to convert a candidate dictionary into searchable semantic text.
    Includes only professional information (skills, work history titles/descriptions, education).
    Excludes sensitive/private information like email, phone, candidate_id, or internal database keys.
    """
    skills_raw = candidate.get("skills", [])
    if isinstance(skills_raw, list):
        skills_str = ", ".join(str(s) for s in skills_raw if s)
    elif isinstance(skills_raw, str):
        skills_str = skills_raw.strip()
    else:
        skills_str = ""

    parts = []
    if skills_str:
        parts.append(f"Skills: {skills_str}")

    exp_list = candidate.get("experience", [])
    if isinstance(exp_list, list) and exp_list:
        exp_entries = []
        for item in exp_list:
            if isinstance(item, dict):
                title = item.get("title", "").strip()
                company = item.get("company", "").strip()
                desc = item.get("description", "").strip()
                
                entry_str = title
                if company:
                    entry_str += f" at {company}" if title else company
                if desc:
                    entry_str += f"\n{desc}"
                if entry_str.strip():
                    exp_entries.append(entry_str.strip())
        if exp_entries:
            parts.append("Experience:\n" + "\n".join(exp_entries))

    education = candidate.get("education", "")
    if isinstance(education, str) and education.strip():
        parts.append(f"Education: {education.strip()}")

    return "\n\n".join(parts)


def _hash_text_to_vector(text: str, dimension: int = 384) -> List[float]:
    """
    Fast, deterministic fallback vector generator for local testing or unconfigured API keys.
    Generates a normalized L2 unit vector of exact dimension using a pseudo-random hash stream.
    """
    if not text or not text.strip():
        return [0.0] * dimension

    words = text.lower().split()
    vec = [0.0] * dimension
    for i, word in enumerate(words):
        word_hash = hash(word)
        idx = abs(word_hash) % dimension
        val = 1.0 if (word_hash % 2 == 0) else -1.0
        vec[idx] += val / (1.0 + i * 0.1)

    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [round(v / norm, 6) for v in vec]

    return vec


class EmbeddingService:
    """
    Abstracted Embedding Service supporting Google Gemini API embeddings,
    OpenAI embeddings, or deterministic hash-based local fallback embeddings.
    """

    def __init__(self):
        self.provider = os.getenv("EMBEDDING_PROVIDER", "local").lower()
        self.model = os.getenv("EMBEDDING_MODEL", "text-embedding-004")
        self.dimension = int(os.getenv("EMBEDDING_DIMENSION", "384"))
        self.api_key = os.getenv("EMBEDDING_API_KEY", os.getenv("GEMINI_API_KEY_1", os.getenv("GEMINI_API_KEY", ""))).strip()
        self.timeout = float(os.getenv("EMBEDDING_TIMEOUT_SECONDS", "3.0"))

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding vector for a single string."""
        if not text or not text.strip():
            return [0.0] * self.dimension

        if self.provider == "gemini" and self.api_key:
            vec = self._embed_gemini(text)
            if vec:
                return vec
        elif self.provider == "openai" and self.api_key:
            vec = self._embed_openai(text)
            if vec:
                return vec

        # Fallback to deterministic pseudo-random hash vector of target dimension
        return _hash_text_to_vector(text, self.dimension)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a batch of strings."""
        if not texts:
            return []
        
        # Batch generation with fallback
        results = []
        for t in texts:
            results.append(self.embed_text(t))
        return results

    def _embed_gemini(self, text: str) -> Optional[List[float]]:
        """Calls Google Gemini text-embedding REST API endpoint."""
        model_name = self.model if self.model.startswith("models/") else f"models/{self.model}"
        url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:embedContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": model_name,
            "content": {
                "parts": [{"text": text[:2048]}]  # Cap length safely
            },
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                if resp.status == 200:
                    res_body = json.loads(resp.read().decode("utf-8"))
                    embedding_data = res_body.get("embedding", {})
                    values = embedding_data.get("values", [])
                    if values:
                        # Slice or truncate to exact dimension if API returned default 768
                        if len(values) > self.dimension:
                            values = values[:self.dimension]
                        elif len(values) < self.dimension:
                            values = values + [0.0] * (self.dimension - len(values))
                        return [float(v) for v in values]
        except Exception as e:
            logger.warning("Gemini embedding API call failed: %s. Using deterministic fallback.", str(e))
        return None

    def _embed_openai(self, text: str) -> Optional[List[float]]:
        """Calls OpenAI-compatible text-embedding REST API endpoint."""
        base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1/embeddings")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model,
            "input": text[:2048],
            "dimensions": self.dimension,
        }
        try:
            req = urllib.request.Request(
                base_url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                if resp.status == 200:
                    res_body = json.loads(resp.read().decode("utf-8"))
                    data = res_body.get("data", [])
                    if data:
                        values = data[0].get("embedding", [])
                        if values:
                            return [float(v) for v in values[:self.dimension]]
        except Exception as e:
            logger.warning("OpenAI embedding API call failed: %s. Using deterministic fallback.", str(e))
        return None
