import os
import json
import hashlib
import logging
from typing import Any, Dict, Optional
import redis.asyncio as redis
from redis.exceptions import RedisError

logger = logging.getLogger("scoutgrid.cache")


class CacheService:
    """
    Resilient Redis Caching Service for ScoutGrid.
    Provides async get/set/delete operations for search results and agent responses.
    Fails gracefully without throwing exceptions if Redis is unavailable or errors out.
    """

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.search_ttl = int(os.getenv("SEARCH_CACHE_TTL", "600"))
        self.agent_ttl = int(os.getenv("AGENT_CACHE_TTL", "1800"))
        self._client: Optional[redis.Redis] = None

    def _get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(
                self.redis_url,
                socket_timeout=2.0,
                socket_connect_timeout=2.0,
                decode_responses=True,
            )
        return self._client

    @staticmethod
    def generate_hash(data: Any) -> str:
        """Generates a deterministic MD5 hash string from a string or dict object."""
        if isinstance(data, str):
            raw_bytes = data.strip().lower().encode("utf-8")
        else:
            raw_bytes = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
        return hashlib.md5(raw_bytes).hexdigest()

    def make_search_key(self, params: Dict[str, Any]) -> str:
        """Creates key format scoutgrid:search:{hash} from full search parameter set."""
        h = self.generate_hash(params)
        return f"scoutgrid:search:{h}"

    def make_agent_key(self, query: str) -> str:
        """Creates key format scoutgrid:agent:{hash} from requirement extraction query."""
        h = self.generate_hash(query.strip().lower())
        return f"scoutgrid:agent:{h}"

    async def get(self, key: str) -> Optional[Any]:
        """
        Fetches and deserializes cached value for a key.
        Returns None on cache miss or Redis connection error.
        """
        try:
            client = self._get_client()
            raw_val = await client.get(key)
            if raw_val is None:
                logger.info("CACHE MISS key=%s", key)
                return None

            logger.info("CACHE HIT key=%s", key)
            return json.loads(raw_val)
        except (RedisError, ConnectionError, OSError) as e:
            logger.warning("REDIS ERROR during get key=%s: %s", key, str(e))
            return None
        except Exception as e:
            logger.warning("CACHE DESERIALIZATION ERROR key=%s: %s", key, str(e))
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Serializes and stores value under key with specified or default TTL.
        Returns True on success, False on error.
        """
        try:
            client = self._get_client()
            serialized = json.dumps(value, default=str)
            effective_ttl = ttl if ttl is not None else self.search_ttl
            await client.set(key, serialized, ex=effective_ttl)
            logger.info("CACHE SET key=%s ttl=%s", key, effective_ttl)
            return True
        except (RedisError, ConnectionError, OSError) as e:
            logger.warning("REDIS ERROR during set key=%s: %s", key, str(e))
            return False
        except Exception as e:
            logger.warning("CACHE SERIALIZATION ERROR key=%s: %s", key, str(e))
            return False

    async def delete(self, key: str) -> bool:
        """Deletes a key from Redis."""
        try:
            client = self._get_client()
            await client.delete(key)
            logger.info("CACHE DELETE key=%s", key)
            return True
        except (RedisError, ConnectionError, OSError) as e:
            logger.warning("REDIS ERROR during delete key=%s: %s", key, str(e))
            return False
