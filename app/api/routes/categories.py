from typing import List, Union, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from bson.errors import InvalidId
from bson.objectid import ObjectId

from app.core.config import settings
from app.db.provider import get_db
from app.services.factory import get_category_service
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryMongoResponse

# Get service
category_service = get_category_service()

# Create router
router = APIRouter()

@router.get("/", response_model=List[CategoryMongoResponse])
async def get_categories(
    skip: int = 0, 
    limit: int = 100,
    db = Depends(get_db())
):
    """Get all categories with pagination"""
    return category_service.get_categories(db, skip=skip, limit=limit)

@router.post("/", response_model=CategoryMongoResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_in: CategoryCreate, 
    db = Depends(get_db())
):
    """Create a new category"""
    return category_service.create_category(db, category_in=category_in)

@router.get("/{category_id}", response_model=CategoryMongoResponse)
async def get_category(
    category_id: str, 
    db = Depends(get_db())
):
    """Get a category by ID"""
    # Validate MongoDB ObjectId format
    try:
        ObjectId(category_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid MongoDB ID format")
    
    category = category_service.get_category(db, category_id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.put("/{category_id}", response_model=CategoryMongoResponse)
async def update_category(
    category_id: str, 
    category_in: CategoryUpdate, 
    db = Depends(get_db())
):
    """Update a category"""
    # Validate MongoDB ObjectId format
    try:
        ObjectId(category_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid MongoDB ID format")
    
    category = category_service.update_category(db, category_id=category_id, category_in=category_in)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.delete("/{category_id}", response_model=CategoryMongoResponse)
async def delete_category(
    category_id: str, 
    db = Depends(get_db())
):
    """Delete a category"""
    # Validate MongoDB ObjectId format
    try:
        ObjectId(category_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid MongoDB ID format")
    
    category = category_service.delete_category(db, category_id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category