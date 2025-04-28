from typing import List, Optional, Dict, Any
from app.repositories.base_mongodb import BaseMongoRepository
from app.schemas.category import CategoryCreate, CategoryUpdate

class CategoryMongoRepository(BaseMongoRepository):
    """Repository for categories in MongoDB"""
    
    def __init__(self):
        super().__init__("categories")
    
    def get_categories(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all categories with pagination"""
        return self.get_multi(skip=skip, limit=limit)
    
    def get_category(self, category_id: str) -> Optional[Dict[str, Any]]:
        """Get category by ID"""
        return self.get(category_id)
    
    def get_category_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get category by name"""
        results = self.get_by_filter({"name": name}, limit=1)
        return results[0] if results else None
    
    def create_category(self, category: CategoryCreate) -> Dict[str, Any]:
        """Create a new category"""
        category_data = category.dict()
        return self.create(category_data)
    
    def update_category(self, category_id: str, category: CategoryUpdate) -> Optional[Dict[str, Any]]:
        """Update a category"""
        category_data = category.dict(exclude_unset=True)
        return self.update(category_id, category_data)
    
    def delete_category(self, category_id: str) -> bool:
        """Delete a category"""
        return self.remove(category_id)

# Create instance for dependency injection
category_repository = CategoryMongoRepository()
