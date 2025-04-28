from typing import Optional, List, Union, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_serializer

# Base Pydantic model for common Category attributes
class CategoryBase(BaseModel):
    """Base model for Category with common attributes"""
    name: str = Field(..., min_length=1, max_length=100, description="Name of the category")
    description: Optional[str] = Field(None, max_length=255, description="Description of the category")

# Model for creating a new Category
class CategoryCreate(CategoryBase):
    """Schema for creating a new Category"""
    pass

# Model for updating an existing Category
class CategoryUpdate(BaseModel):
    """Schema for updating an existing Category"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Name of the category")
    description: Optional[str] = Field(None, max_length=255, description="Description of the category")

# Simplified MongoDB Note representation for use in CategoryMongoResponse
class MongoNoteInCategory(BaseModel):
    """Simplified Note model for MongoDB Category responses"""
    id: str
    title: str

# Response model for MongoDB Category
class CategoryMongoResponse(CategoryBase):
    """Schema for Category response data with MongoDB"""
    id: str
    created_at: datetime
    updated_at: datetime
    notes_count: Optional[int] = 0
    
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: datetime) -> str:
        return dt.isoformat()

# Alias for backward compatibility
CategoryResponse = CategoryMongoResponse