import os
import logging
import asyncio
import motor.motor_asyncio
from pymongo import ASCENDING, IndexModel

logger = logging.getLogger(__name__)

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE", "scoutgrid")

_client: motor.motor_asyncio.AsyncIOMotorClient | None = None
_db: motor.motor_asyncio.AsyncIOMotorDatabase | None = None


def get_db() -> motor.motor_asyncio.AsyncIOMotorDatabase:
    global _client, _db
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None

    # Re-initialize client if missing or if running in a different event loop
    if _client is None or getattr(_client, 'io_loop', None) != current_loop:
        _client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
        _db = _client[MONGODB_DATABASE]

    return _db


def get_candidates_collection() -> motor.motor_asyncio.AsyncIOMotorCollection:
    return get_db()["candidates"]


async def connect_to_mongo() -> None:
    global _client, _db

    logger.info("Connecting to MongoDB at %s", MONGODB_URI)
    db = get_db()
    _client = db.client

    # Verify connectivity
    await _client.admin.command("ping")
    logger.info("Connected to MongoDB database '%s'", MONGODB_DATABASE)

    await _create_indexes()


async def close_mongo_connection() -> None:
    global _client, _db

    if _client is not None:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed.")


async def _create_indexes() -> None:
    collection = get_candidates_collection()

    indexes = [
        IndexModel([("location", ASCENDING)], name="idx_location"),
        IndexModel([("skills", ASCENDING)], name="idx_skills"),
        IndexModel([("experience_years", ASCENDING)], name="idx_experience_years"),
        IndexModel([("experience.title", ASCENDING)], name="idx_experience_title"),
        IndexModel([("skills", ASCENDING), ("location", ASCENDING), ("experience_years", ASCENDING)], name="idx_combined_search"),
    ]

    await collection.create_indexes(indexes)
    logger.info("MongoDB indexes ensured.")

