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

def get_nlq_parser_service():
    """Get the natural language query parser service"""
    from app.services.nlq_parser import nlq_parser_service
    return nlq_parser_service

def get_vector_store_service():
    """Get the vector store service for embedding-based search"""
    from app.services.vector_store import vector_store
    return vector_store