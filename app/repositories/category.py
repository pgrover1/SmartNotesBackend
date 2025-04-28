from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models.category import Category
from app.models.note import Note, note_category
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.repositories.base import BaseRepository

class CategoryRepository(BaseRepository[Category, CategoryCreate, CategoryUpdate]):
    """Repository for Category operations"""
    
    def __init__(self):
        """Initialize with Category model"""
        super().__init__(Category)
    
    def get_with_notes_count(self, db: Session, id: int) -> Optional[dict]:
        """Get category with count of associated notes"""
        result = (
            db.query(
                Category, 
                func.count(note_category.c.note_id).label("notes_count")
            )
            .outerjoin(note_category, Category.id == note_category.c.category_id)
            .filter(Category.id == id)
            .group_by(Category.id)
            .first()
        )
        
        if not result:
            return None
            
        category, notes_count = result
        # Add notes_count to category object
        setattr(category, "notes_count", notes_count)
        return category
    
    def get_multi_with_notes_count(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[dict]:
        """Get multiple categories with count of associated notes"""
        results = (
            db.query(
                Category, 
                func.count(note_category.c.note_id).label("notes_count")
            )
            .outerjoin(note_category, Category.id == note_category.c.category_id)
            .group_by(Category.id)
            .order_by(Category.name)
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        # Add notes_count to each category object
        categories = []
        for category, notes_count in results:
            setattr(category, "notes_count", notes_count)
            categories.append(category)
            
        return categories

# Create instance for dependency injection
category_repository = CategoryRepository()
