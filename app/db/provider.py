from app.core.config import settings
from functools import lru_cache

@lru_cache()
def get_db():
    """Get the MongoDB database provider"""
    from app.db.mongodb import get_db as mongodb_get_db
    return mongodb_get_db