"""Factory module for AI services"""
from app.core.config import settings

def get_ai_services():
    """Get all AI services in a dictionary"""
    from app.services.categorization import categorization_service
    from app.services.note_analysis import note_analysis_service
    
    # Return all services in a dictionary for easy access
    return {
        "categorization": categorization_service,
        "note_analysis": note_analysis_service
    }