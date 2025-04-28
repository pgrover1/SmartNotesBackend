from typing import List, Optional, Dict, Any
from app.repositories.base_mongodb import BaseMongoRepository
from app.schemas.note import NoteCreate, NoteUpdate

class NoteMongoRepository(BaseMongoRepository):
    """Repository for notes in MongoDB"""
    
    def __init__(self):
        super().__init__("notes")
    
    def get_notes(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all notes with pagination"""
        return self.get_multi(skip=skip, limit=limit)
    
    def get_note(self, note_id: str) -> Optional[Dict[str, Any]]:
        """Get note by ID"""
        return self.get(note_id)
    
    def get_notes_by_category(self, category_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get notes by category ID"""
        return self.get_by_filter({"category_ids": category_id}, skip=skip, limit=limit)
    
    def create_note(self, note: NoteCreate) -> Dict[str, Any]:
        """Create a new note"""
        note_data = note.dict()
        # Convert category_ids to a list if provided
        if note_data.get("category_ids"):
            note_data["category_ids"] = list(note_data["category_ids"])
        return self.create(note_data)
    
    def update_note(self, note_id: str, note: NoteUpdate) -> Optional[Dict[str, Any]]:
        """Update a note"""
        note_data = note.dict(exclude_unset=True)
        # Convert category_ids to a list if provided
        if note_data.get("category_ids"):
            note_data["category_ids"] = list(note_data["category_ids"])
        return self.update(note_id, note_data)
    
    def delete_note(self, note_id: str) -> bool:
        """Delete a note"""
        return self.remove(note_id)
    
    def search_notes(self, keyword: Optional[str] = None, category_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Search notes by keyword and/or category"""
        filter_dict = {}
        
        # Filter by keyword if provided
        if keyword:
            filter_dict["$or"] = [
                {"title": {"$regex": keyword, "$options": "i"}},
                {"content": {"$regex": keyword, "$options": "i"}}
            ]
        
        # Filter by category if provided
        if category_id:
            filter_dict["category_ids"] = category_id
        
        return self.get_by_filter(filter_dict, skip=skip, limit=limit)

# Create instance for dependency injection
note_repository = NoteMongoRepository()
