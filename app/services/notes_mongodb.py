from typing import List, Optional, Dict, Any
from app.repositories.note_mongodb import note_repository
from app.repositories.category_mongodb import category_repository
from app.schemas.note import NoteCreate, NoteUpdate, NoteSearchQuery
from app.services.factory_ai import get_ai_services

# Get AI services
ai_services = get_ai_services()
categorization_service = ai_services["categorization"]
note_analysis_service = ai_services["note_analysis"]

class NoteMongoService:
    """Service for note operations with MongoDB"""
    
    def get_note(self, db, note_id: str) -> Optional[Dict[str, Any]]:
        """Get a note by ID"""
        return note_repository.get_note(note_id)
    
    def get_notes(self, db, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all notes with pagination"""
        return note_repository.get_notes(skip=skip, limit=limit)
    
    def get_notes_without_categories(self, db) -> List[Dict[str, Any]]:
        """Get notes that don't have any categories"""
        # Find notes where category_ids is empty or doesn't exist
        return note_repository.get_by_filter({
            "$or": [
                {"category_ids": {"$exists": False}},
                {"category_ids": {"$size": 0}},
                {"category_ids": None}
            ]
        })
    
    def add_note_to_category(self, db, note_id: str, category_id: str) -> Optional[Dict[str, Any]]:
        """Add a note to a category"""
        # Get note and category
        note = note_repository.get_note(note_id)
        category = category_repository.get_category(category_id)
        
        if not note or not category:
            return None
        
        # Initialize category_ids if it doesn't exist
        if "category_ids" not in note:
            note["category_ids"] = []
        elif not isinstance(note["category_ids"], list):
            note["category_ids"] = []
        
        # Check if already in category
        if category_id not in note["category_ids"]:
            # Add category to note
            note["category_ids"].append(category_id)
            return note_repository.update_note(note_id, {"category_ids": note["category_ids"]})
        
        return note
    
    def create_note(self, db, note_in: NoteCreate) -> Dict[str, Any]:
        """Create a new note"""
        # Create the note directly without AI enhancements
        return note_repository.create_note(note_in)
    
    def update_note(self, db, note_id: str, note_in: NoteUpdate) -> Optional[Dict[str, Any]]:
        """Update an existing note"""
        db_note = note_repository.get_note(note_id)
        if not db_note:
            return None
        
        # Update note directly without AI enhancements
        note_data = note_in.dict(exclude_unset=True)
        return note_repository.update_note(note_id, note_data)
    
    def delete_note(self, db, note_id: str) -> Optional[Dict[str, Any]]:
        """Delete a note"""
        note = note_repository.get_note(note_id)
        if not note:
            return None
        
        if note_repository.delete_note(note_id):
            return note
        return None
    
    def search_notes(self, db, query: NoteSearchQuery, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Search notes by various criteria"""
        # If natural language query is provided, extract keywords from it
        if query.natural_language_query:
            # Extract keywords from the query using categorization service's keyword extraction
            keywords = categorization_service.extract_keywords(query.natural_language_query)
            
            # Use the most relevant keyword as search term
            keyword = " ".join(keywords[:2]) if keywords else None
            category_id = None
            
            # Override with extracted parameters if available
            if keyword:
                query.keyword = keyword
            if category_id:
                query.category_id = category_id
        
        # Perform search with processed parameters
        return note_repository.search_notes(
            keyword=query.keyword,
            category_id=query.category_id,
            skip=skip, 
            limit=limit
        )
    # Create instance for dependency injection
note_mongo_service = NoteMongoService()
