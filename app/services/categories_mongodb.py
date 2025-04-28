from typing import List, Optional, Dict, Any, Tuple
from app.repositories.category_mongodb import category_repository
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services.factory_ai import get_ai_services

# Get AI services
ai_services = get_ai_services()
categorization_service = ai_services["categorization"]

class CategoryMongoService:
    """Service for category operations with MongoDB"""
    
    def get_category(self, db, category_id: str) -> Optional[Dict[str, Any]]:
        """Get a category by ID"""
        return category_repository.get_category(category_id)
    
    def get_categories(self, db, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all categories with pagination"""
        return category_repository.get_categories(skip=skip, limit=limit)
    
    def create_category(self, db, category_in: CategoryCreate) -> Dict[str, Any]:
        """Create a new category"""
        # Check if category with same name already exists
        existing = category_repository.get_category_by_name(category_in.name)
        if existing:
            return existing
        
        return category_repository.create_category(category_in)
    
    def update_category(self, db, category_id: str, category_in: CategoryUpdate) -> Optional[Dict[str, Any]]:
        """Update a category"""
        db_category = category_repository.get_category(category_id)
        if not db_category:
            return None
            
        # Check if updating to a name that already exists
        if category_in.name and category_in.name != db_category.get("name"):
            existing = category_repository.get_category_by_name(category_in.name)
            if existing:
                return None
                
        return category_repository.update_category(category_id, category_in)
    
    def delete_category(self, db, category_id: str) -> Optional[Dict[str, Any]]:
        """Delete a category"""
        category = category_repository.get_category(category_id)
        if not category:
            return None
            
        if category_repository.delete_category(category_id):
            return category
        return None
    
    def suggest_category(self, db, content: str) -> Optional[str]:
        """Suggest a category for content using AI"""
        # Get all categories
        categories = category_repository.get_categories()
        if not categories:
            return None
            
        # Format category data for AI service
        category_data = [(cat["id"], cat["name"]) for cat in categories]
        
        # Use categorization service to suggest the best matching category
        result = categorization_service.suggest_category("", content)
        
        # Find matching category by name
        for cat_id, cat_name in category_data:
            if cat_name == result["category"]:
                return cat_id
                
        return None

# Create instance for dependency injection
category_mongo_service = CategoryMongoService()