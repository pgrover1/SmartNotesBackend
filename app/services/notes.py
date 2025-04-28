from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.repositories.note import note_repository
from app.repositories.category import category_repository
from app.models.note import Note, note_category
from app.models.category import Category
from app.schemas.note import NoteCreate, NoteUpdate, NoteSearchQuery
from app.services.factory_ai import get_ai_services

# Get AI services
ai_services = get_ai_services()
categorization_service = ai_services["categorization"]
note_analysis_service = ai_services["note_analysis"]

class NoteService:
    """Service for note operations with business logic"""
    
    def get_note(self, db: Session, note_id: int) -> Optional[Note]:
        """Get a note by ID"""
        return note_repository.get_with_categories(db, note_id)
    
    def get_notes(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Note]:
        """Get all notes with pagination"""
        return note_repository.get_multi_with_categories(db, skip=skip, limit=limit)
    
    def get_notes_without_categories(self, db: Session) -> List[Note]:
        """Get notes that don't have any categories"""
        # Query for notes not in the note_category table
        notes_with_categories = db.query(note_category.c.note_id).distinct()
        notes = db.query(Note).filter(
            ~Note.id.in_(notes_with_categories)
        ).all()
        return notes
    
    def add_note_to_category(self, db: Session, note_id: int, category_id: int) -> Optional[Note]:
        """Add a note to a category"""
        # Get note and category
        note = note_repository.get_with_categories(db, note_id)
        category = category_repository.get(db, category_id)
        
        if not note or not category:
            return None
            
        # Check if already in category
        if category not in note.categories:
            note.categories.append(category)
            db.add(note)
            db.commit()
            db.refresh(note)
            
        return note
    
    def create_note(self, db: Session, note_in: NoteCreate) -> Note:
        """Create a new note"""
        # Create the note directly without AI enhancements
        return note_repository.create_with_categories(db, obj_in=note_in)
    
    def update_note(self, db: Session, note_id: int, note_in: NoteUpdate) -> Optional[Note]:
        """Update an existing note"""
        db_note = note_repository.get(db, note_id)
        if not db_note:
            return None
            
        # Update note directly without AI enhancements
        return note_repository.update_with_categories(db, db_obj=db_note, obj_in=note_in)
    
    def delete_note(self, db: Session, note_id: int) -> Optional[Note]:
        """Delete a note"""
        return note_repository.remove(db, id=note_id)
    
    def search_notes(
        self, 
        db: Session, 
        query: NoteSearchQuery,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Note]:
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
        return note_repository.search(
            db, 
            keyword=query.keyword,
            category_id=query.category_id,
            skip=skip, 
            limit=limit
        )
    # Create instance for dependency injection
note_service = NoteService()
