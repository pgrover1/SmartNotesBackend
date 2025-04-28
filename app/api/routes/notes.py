from typing import List, Optional, Union, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from bson.errors import InvalidId
from bson.objectid import ObjectId

from app.core.config import settings
from app.db.provider import get_db
from app.services.factory import get_note_service, get_category_service, get_categorization_service, get_note_analysis_service
from app.schemas.note import NoteCreate, NoteUpdate, NoteResponse, NoteSearchQuery, NoteMongoResponse

# Get services
note_service = get_note_service()
category_service = get_category_service()
categorization_service = get_categorization_service()
note_analysis_service = get_note_analysis_service()

# Create router
router = APIRouter()

@router.get("/", response_model=List[NoteMongoResponse])
async def get_notes(
    skip: int = 0, 
    limit: int = 100,
    db = Depends(get_db())
):
    """Get all notes with pagination"""
    return note_service.get_notes(db, skip=skip, limit=limit)

@router.post("/", response_model=NoteMongoResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    note_in: NoteCreate, 
    db = Depends(get_db())
):
    """Create a new note"""
    return note_service.create_note(db, note_in=note_in)

@router.get("/{note_id}", response_model=NoteMongoResponse)
async def get_note(
    note_id: str, 
    db = Depends(get_db())
):
    """Get a note by ID"""
    # Validate MongoDB ObjectId format
    try:
        ObjectId(note_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid MongoDB ID format")
    
    note = note_service.get_note(db, note_id=note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

@router.put("/{note_id}", response_model=NoteMongoResponse)
async def update_note(
    note_id: str, 
    note_in: NoteUpdate, 
    db = Depends(get_db())
):
    """Update a note"""
    # Validate MongoDB ObjectId format
    try:
        ObjectId(note_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid MongoDB ID format")
    
    note = note_service.update_note(db, note_id=note_id, note_in=note_in)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

@router.delete("/{note_id}", response_model=NoteMongoResponse)
async def delete_note(
    note_id: str, 
    db = Depends(get_db())
):
    """Delete a note"""
    # Validate MongoDB ObjectId format
    try:
        ObjectId(note_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid MongoDB ID format")
    
    note = note_service.delete_note(db, note_id=note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

@router.post("/search", response_model=List[NoteMongoResponse])
async def search_notes(
    query: NoteSearchQuery,
    skip: int = 0, 
    limit: int = 100,
    db = Depends(get_db())
):
    """Search notes by various criteria"""
    return note_service.search_notes(db, query=query, skip=skip, limit=limit)

@router.post("/{note_id}/suggest-category", response_model=Dict[str, Any])
async def suggest_category_for_note(
    note_id: str,
    db = Depends(get_db())
):
    """Suggest a category for a note based on its title and content"""
    # Validate MongoDB ObjectId format
    try:
        ObjectId(note_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid MongoDB ID format")
    
    note = note_service.get_note(db, note_id=note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Get title and content from note object
    title = note.get('title', '')
    content = note.get('content', '')
    
    # Use categorization service to suggest a category
    result = categorization_service.suggest_category(title, content)
    
    return result

@router.get("/{note_id}/sentiment", response_model=Dict[str, str])
async def get_note_sentiment(
    note_id: str,
    db = Depends(get_db())
):
    """Get the sentiment analysis of a note"""
    # Validate MongoDB ObjectId format
    try:
        ObjectId(note_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid MongoDB ID format")
    
    note = note_service.get_note(db, note_id=note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Get content from note object
    content = note.get('content', '')
    
    if not content:
        raise HTTPException(status_code=400, detail="Note has no content to analyze")
    
    # Get sentiment analysis only
    sentiment = note_analysis_service.analyze_sentiment(content)
    
    return {"sentiment": sentiment}

@router.get("/{note_id}/summarize", response_model=Dict[str, Any])
async def summarize_note(
    note_id: str,
    max_length: int = Query(150, description="Maximum length of summary in characters"),
    model: str = Query("gpt-4o", description="OpenAI model to use: gpt-4o or gpt-3.5-turbo"),
    db = Depends(get_db())
):
    """Generate a summary of a note using OpenAI"""
    # Validate MongoDB ObjectId format
    try:
        ObjectId(note_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid MongoDB ID format")
    
    note = note_service.get_note(db, note_id=note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Get title and content from note object
    title = note.get('title', '')
    content = note.get('content', '')
    
    if not content:
        raise HTTPException(status_code=400, detail="Note has no content to summarize")
    
    # Validate model parameter
    if model not in ["gpt-4o", "gpt-3.5-turbo"]:
        raise HTTPException(status_code=400, detail="Model must be either gpt-4o or gpt-3.5-turbo")
        
    # Use note analysis service for customized summarization
    result = note_analysis_service.generate_openai_summary(title, content, max_length=max_length, model=model)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"] or "Failed to generate summary")
    
    return result