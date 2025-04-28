from typing import List, Optional, Union, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field, field_serializer

# Base Pydantic model for common Note attributes
class NoteBase(BaseModel):
    """Base model for Note with common attributes"""
    title: str = Field(..., min_length=1, max_length=255, description="Title of the note")
    content: str = Field(..., min_length=1, description="Content of the note")

# Model for creating a new Note
class NoteCreate(NoteBase):
    """Schema for creating a new Note"""
    category_ids: Optional[List[str]] = Field(default=[], description="List of category IDs to associate with the note")

# Model for updating an existing Note
class NoteUpdate(BaseModel):
    """Schema for updating an existing Note"""
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Title of the note")
    content: Optional[str] = Field(None, min_length=1, description="Content of the note")
    category_ids: Optional[List[str]] = Field(None, description="List of category IDs to associate with the note")

# MongoDB Category representation for use in NoteMongoResponse
class MongoCategory(BaseModel):
    """Simplified Category model for MongoDB responses"""
    id: str
    name: str

# Response model for MongoDB Note
class NoteMongoResponse(NoteBase):
    """Schema for Note response data with MongoDB"""
    id: str
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    category_ids: List[str] = []
    categories: List[MongoCategory] = []
    created_at: datetime
    updated_at: datetime
    
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: datetime) -> str:
        return dt.isoformat()

# Alias for backward compatibility
NoteResponse = NoteMongoResponse

# Query model for note search
class NoteSearchQuery(BaseModel):
    """Schema for note search queries"""
    keyword: Optional[str] = Field(None, description="Keyword to search in title and content")
    category_id: Optional[str] = Field(None, description="Filter by category ID")
    natural_language_query: Optional[str] = Field(None, description="Natural language query for searching notes")