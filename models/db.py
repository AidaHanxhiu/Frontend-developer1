import os
from typing import Optional
from urllib.parse import urlparse

from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables once when the module is imported
load_dotenv()


_client = None


def _clean_uri(uri: str) -> str:
    """Strip extra quotes/whitespace around the URI string."""
    return uri.strip().strip('"').strip("'")


def _extract_db_name(uri: str) -> Optional[str]:
    """Get database name from the URI path, if present."""
    parsed = urlparse(uri)
    path = parsed.path.lstrip("/")
    return path.split("/")[0].split("?")[0] if path else None


def _get_client(uri: str) -> MongoClient:
    """Reuse a single MongoClient instance."""
    global _client
    if _client is None:
        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    return _client


def get_db():
    """
    Return a MongoDB database instance using a single, shared connection.

    Uses MONGODB_URI (or MONGO_URI) from the environment. If the URI does not
    include a database name, it falls back to MONGODB_DBNAME (or 'library').
    """
    raw_uri = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI") or "mongodb://localhost:27017/library"
    mongodb_uri = _clean_uri(raw_uri)

    client = _get_client(mongodb_uri)

    # Prefer the database encoded in the URI (e.g., mongodb://.../mydb)
    default_db = client.get_default_database()
    if default_db:
        return default_db

    # Otherwise, derive from the path or fallback environment variable
    db_name = _extract_db_name(mongodb_uri) or os.getenv("MONGODB_DBNAME") or "library"
    return client[db_name]