from typing import List, Optional, Union, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from bson.errors import InvalidId
from bson.objectid import ObjectId

from app.core.config import settings
from app.db.provider import get_db
from app.services.factory import get_note_service, get_category_service, get_categorization_service, get_note_analysis_service, get_vector_store_service, get_nlq_parser_service
from app.schemas.note import NoteCreate, NoteUpdate, NoteResponse, NoteSearchQuery, NoteMongoResponse
from app.repositories.note_mongodb import note_repository
import logging

# Setup logging
logger = logging.getLogger(__name__)

# Get services
note_service = get_note_service()
category_service = get_category_service()
categorization_service = get_categorization_service()
note_analysis_service = get_note_analysis_service()
vector_store = get_vector_store_service()
nlq_parser_service = get_nlq_parser_service()

# Create router
router = APIRouter()

@router.get("/", response_model=List[NoteMongoResponse])
async def get_notes(
    skip: int = 0, 
    limit: int = 100,
    db = Depends(get_db())
):
    """Get all notes with pagination"""
    notes = note_service.get_notes(db, skip=skip, limit=limit)
    
    # Enhance each note with categories
    from app.dependencies import enhance_note_with_categories
    enhanced_notes = [enhance_note_with_categories(note, db) for note in notes]
    
    return enhanced_notes

@router.post("/", response_model=NoteMongoResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    note_in: NoteCreate, 
    db = Depends(get_db())
):
    """Create a new note"""
    note = note_service.create_note(db, note_in=note_in)
    
    # Enhance note with categories
    from app.dependencies import enhance_note_with_categories
    enhanced_note = enhance_note_with_categories(note, db)
    
    return enhanced_note

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
    
    # Enhance note with categories
    from app.dependencies import enhance_note_with_categories
    enhanced_note = enhance_note_with_categories(note, db)
    
    return enhanced_note

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
    
    # Enhance note with categories
    from app.dependencies import enhance_note_with_categories
    enhanced_note = enhance_note_with_categories(note, db)
    
    return enhanced_note

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
    
    # Enhance note with categories
    from app.dependencies import enhance_note_with_categories
    enhanced_note = enhance_note_with_categories(note, db)
    
    return enhanced_note

@router.post("/search", response_model=List[NoteMongoResponse])
async def search_notes(
    query: NoteSearchQuery,
    skip: int = 0, 
    limit: int = 100,
    db = Depends(get_db())
):
    """Search notes by various criteria
    
    Supports natural language queries like:
    - "Find my meeting notes from last Monday"
    - "Show me all notes about project X with more than 100 words"
    - "Get my personal notes from last month"
    """
    notes = note_service.search_notes(db, query=query, skip=skip, limit=limit)
    
    # Enhance each note with categories
    from app.dependencies import enhance_note_with_categories
    enhanced_notes = [enhance_note_with_categories(note, db) for note in notes]
    
    return enhanced_notes

@router.post("/rebuild-vector-store", response_model=Dict[str, Any])
async def rebuild_vector_store(
    clear_existing: bool = Query(False, description="Clear existing vector store before rebuilding"),
    db = Depends(get_db())
):
    """Rebuild the vector store with all notes in the database
    
    This is useful after importing notes or if the vector search is not working correctly.
    It will create embeddings for all notes in the database and store them in the vector store.
    
    - Set clear_existing=true to remove all existing embeddings before rebuilding
    """
    count = note_service.rebuild_vector_store(db, clear_existing=clear_existing)
    
    if clear_existing:
        return {"success": True, "message": f"Vector store cleared and rebuilt with {count} notes"}
    else:
        return {"success": True, "message": f"Vector store updated with {count} notes"}


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