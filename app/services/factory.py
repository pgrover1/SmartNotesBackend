from app.core.config import settings

def get_note_service():
    """Get the MongoDB note service"""
    from app.services.notes import note_mongo_service
    return note_mongo_service

def get_category_service():
    """Get the MongoDB category service"""
    from app.services.categories import category_mongo_service
    return category_mongo_service

def get_categorization_service():
    """Get the categorization service"""
    from app.services.categorization import categorization_service
    return categorization_service

def get_note_analysis_service():
    """Get the note analysis service for summarization and sentiment analysis"""
    from app.services.note_analysis import note_analysis_service
    return note_analysis_service