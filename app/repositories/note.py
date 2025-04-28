from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app.models.note import Note
from app.models.category import Category
from app.schemas.note import NoteCreate, NoteUpdate
from app.repositories.base import BaseRepository

class NoteRepository(BaseRepository[Note, NoteCreate, NoteUpdate]):
    """Repository for Note operations"""
    
    def __init__(self):
        """Initialize with Note model"""
        super().__init__(Note)
    
    def create_with_categories(self, db: Session, *, obj_in: NoteCreate) -> Note:
        """Create a note with category associations"""
        # Extract category_ids from the input and remove from the dict
        category_ids = obj_in.category_ids or []
        obj_in_data = obj_in.dict(exclude={"category_ids"})
        
        # Create note instance
        db_obj = Note(**obj_in_data)
        
        # Add categories if provided
        if category_ids:
            categories = db.query(Category).filter(Category.id.in_(category_ids)).all()
            db_obj.categories = categories
        
        # Save to database
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update_with_categories(self, db: Session, *, db_obj: Note, obj_in: NoteUpdate) -> Note:
        """Update note with category associations"""
        # Extract category_ids if provided
        category_ids = None
        update_data = {}
        
        if isinstance(obj_in, dict):
            update_data = obj_in.copy()
            category_ids = update_data.pop("category_ids", None)
        else:
            update_data = obj_in.dict(exclude_unset=True, exclude={"category_ids"})
            category_ids = obj_in.category_ids
        
        # Update note fields
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        # Update categories if provided
        if category_ids is not None:
            categories = db.query(Category).filter(Category.id.in_(category_ids)).all()
            db_obj.categories = categories
        
        # Save to database
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_with_categories(self, db: Session, id: int) -> Optional[Note]:
        """Get note with eager loaded categories"""
        return db.query(Note).options(joinedload(Note.categories)).filter(Note.id == id).first()
    
    def get_multi_with_categories(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Note]:
        """Get multiple notes with eager loaded categories"""
        return (
            db.query(Note)
            .options(joinedload(Note.categories))
            .order_by(Note.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def search(
        self, 
        db: Session, 
        *, 
        keyword: Optional[str] = None,
        category_id: Optional[int] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Note]:
        """Search notes by keyword and/or category"""
        query = db.query(Note).options(joinedload(Note.categories))
        
        # Filter by keyword if provided
        if keyword:
            search_filter = or_(
                Note.title.ilike(f"%{keyword}%"),
                Note.content.ilike(f"%{keyword}%")
            )
            query = query.filter(search_filter)
        
        # Filter by category if provided
        if category_id:
            query = query.join(Note.categories).filter(Category.id == category_id)
        
        # Execute query with pagination
        return query.order_by(Note.created_at.desc()).offset(skip).limit(limit).all()

# Create instance for dependency injection
note_repository = NoteRepository()
