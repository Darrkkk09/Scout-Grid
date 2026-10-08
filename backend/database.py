import os
import logging
import asyncio
import motor.motor_asyncio
from pymongo import ASCENDING, IndexModel

logger = logging.getLogger(__name__)

_client: motor.motor_asyncio.AsyncIOMotorClient | None = None
_db: motor.motor_asyncio.AsyncIOMotorDatabase | None = None
_client_loop: asyncio.AbstractEventLoop | None = None


def get_database_name() -> str:
    return os.environ.get("MONGODB_DATABASE", "scoutgrid")


def get_db() -> motor.motor_asyncio.AsyncIOMotorDatabase:
    global _client, _db, _client_loop

    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None

    uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
    db_name = get_database_name()

    if _client is None or (current_loop is not None and _client_loop != current_loop):
        _client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        _client_loop = current_loop

    return _client[db_name]


def get_candidates_collection() -> motor.motor_asyncio.AsyncIOMotorCollection:
    return get_db()["candidates"]


async def connect_to_mongo() -> None:
    global _client, _db, _client_loop

    uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
    db_name = get_database_name()
    logger.info("Connecting to MongoDB at %s / database '%s'", uri, db_name)
    db = get_db()
    _client = db.client
    _client_loop = asyncio.get_running_loop()

    # Verify connectivity
    await _client.admin.command("ping")
    logger.info("Connected to MongoDB database '%s'", db_name)

    await _create_indexes()


async def close_mongo_connection() -> None:
    global _client, _db, _client_loop

    if _client is not None:
        _client.close()
        _client = None
        _db = None
        _client_loop = None
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
