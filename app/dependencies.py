from typing import Callable, Optional
from fastapi import Depends, HTTPException, status
from bson.errors import InvalidId
from bson.objectid import ObjectId

from app.db.provider import get_db
from app.services.factory import get_note_service, get_category_service
from app.services.factory_ai import get_ai_services

# Get services for dependency injection
note_service = get_note_service()
category_service = get_category_service()
ai_services = get_ai_services()

def validate_object_id(id_value: str) -> str:
    """Validate that the provided ID is a valid MongoDB ObjectId"""
    try:
        ObjectId(id_value)
        return id_value
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MongoDB ObjectId format"
        )

def get_note_by_id(note_id: str = Depends(validate_object_id), db=Depends(get_db())):
    """Get a note by ID, validating existence"""
    note = note_service.get_note(db, note_id=note_id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    return note

def get_category_by_id(category_id: str = Depends(validate_object_id), db=Depends(get_db())):
    """Get a category by ID, validating existence"""
    category = category_service.get_category(db, category_id=category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category

def get_note_content(note=Depends(get_note_by_id)):
    """Extract content from a note and validate it's not empty"""
    content = note.get('content', '') if isinstance(note, dict) else getattr(note, 'content', '')
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Note has no content to process"
        )
    return content

def get_note_title_and_content(note=Depends(get_note_by_id)):
    """Extract title and content from a note and validate content isn't empty"""
    if isinstance(note, dict):
        title = note.get('title', '')
        content = note.get('content', '')
    else:
        title = getattr(note, 'title', '')
        content = getattr(note, 'content', '')
        
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Note has no content to process"
        )
    return {"title": title, "content": content}

def enhance_note_with_categories(note: dict, db=Depends(get_db())):
    """Enhance note with category information
    
    If note has category IDs, fetch the corresponding categories.
    If no categories, add an 'Uncategorized' category.
    """
    # Initialize categories list
    note['categories'] = []
    
    # Get category IDs from note
    category_ids = note.get('category_ids', [])
    
    # If there are category IDs, fetch the corresponding categories
    if category_ids:
        for cat_id in category_ids:
            try:
                category = category_service.get_category(db, category_id=cat_id)
                if category:
                    note['categories'].append({
                        "id": category["id"],
                        "name": category["name"]
                    })
            except Exception:
                # Skip invalid categories
                pass
    
    # If no categories were found, add 'Uncategorized'
    if not note['categories']:
        note['categories'] = [{
            "id": "uncategorized",
            "name": "Uncategorized"
        }]
    
    return note