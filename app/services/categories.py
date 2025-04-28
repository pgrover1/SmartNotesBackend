from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.repositories.category import category_repository
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services.ai import ai_service

class CategoryService:
    """Service for category operations with business logic"""
    
    def get_category(self, db: Session, category_id: int) -> Optional[Category]:
        """Get a category by ID with notes count"""
        return category_repository.get_with_notes_count(db, category_id)
    
    def get_categories(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Category]:
        """Get all categories with notes count"""
        return category_repository.get_multi_with_notes_count(db, skip=skip, limit=limit)
    
    def create_category(self, db: Session, category_in: CategoryCreate) -> Category:
        """Create a new category"""
        return category_repository.create(db, obj_in=category_in)
    
    def update_category(self, db: Session, category_id: int, category_in: CategoryUpdate) -> Optional[Category]:
        """Update an existing category"""
        db_category = category_repository.get(db, category_id)
        if not db_category:
            return None
        return category_repository.update(db, db_obj=db_category, obj_in=category_in)
    
    def delete_category(self, db: Session, category_id: int) -> Optional[Category]:
        """Delete a category"""
        return category_repository.remove(db, id=category_id)
    
    def suggest_category(self, db: Session, text: str) -> Optional[int]:
        """Suggest a category ID based on text content"""
        # Get all available categories
        categories = self.get_categories(db, limit=100)
        
        if not categories:
            return None
            
        # Extract category names and IDs
        category_data = [(cat.id, cat.name) for cat in categories]
        
        # Use AI to suggest the best matching category
        return ai_service.suggest_category(text, category_data)

# Create instance for dependency injection
category_service = CategoryService()
