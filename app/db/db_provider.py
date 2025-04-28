from app.core.config import settings
from functools import lru_cache

@lru_cache()
def get_db_provider():
    """Factory function to return the appropriate database provider"""
    if settings.USE_MONGODB:
        from app.db.mongodb import get_db
    else:
        from app.db.session import get_db
    
    return get_db
