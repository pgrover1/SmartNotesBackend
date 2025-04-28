from app.core.config import settings

def get_note_repository():
    """Get the appropriate note repository based on configuration"""
    if settings.USE_MONGODB:
        from app.repositories.note_mongodb import note_repository
    else:
        from app.repositories.note import note_repository
    return note_repository

def get_category_repository():
    """Get the appropriate category repository based on configuration"""
    if settings.USE_MONGODB:
        from app.repositories.category_mongodb import category_repository
    else:
        from app.repositories.category import category_repository
    return category_repository
