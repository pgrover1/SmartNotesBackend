from typing import List, Optional, Dict, Any
import logging
from app.repositories.note_mongodb import note_repository
from app.repositories.category_mongodb import category_repository
from app.schemas.note import NoteCreate, NoteUpdate, NoteSearchQuery
from app.services.factory_ai import get_ai_services
from app.services.factory import get_nlq_parser_service, get_vector_store_service

# Setup logging
logger = logging.getLogger(__name__)

# Get AI services
ai_services = get_ai_services()
categorization_service = ai_services["categorization"]
note_analysis_service = ai_services["note_analysis"]

# Get NLQ and vector store services
nlq_parser_service = get_nlq_parser_service()
vector_store = get_vector_store_service()

class NoteMongoService:
    """Service for note operations with MongoDB"""
    
    def get_note(self, db, note_id: str) -> Optional[Dict[str, Any]]:
        """Get a note by ID"""
        return note_repository.get_note(note_id)
    
    def get_notes(self, db, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all notes with pagination"""
        return note_repository.get_notes(skip=skip, limit=limit)
    
    def get_notes_without_categories(self, db) -> List[Dict[str, Any]]:
        """Get notes that don't have any categories"""
        # Find notes where category_ids is empty or doesn't exist
        return note_repository.get_by_filter({
            "$or": [
                {"category_ids": {"$exists": False}},
                {"category_ids": {"$size": 0}},
                {"category_ids": None}
            ]
        })
    
    def add_note_to_category(self, db, note_id: str, category_id: str) -> Optional[Dict[str, Any]]:
        """Add a note to a category"""
        # Get note and category
        note = note_repository.get_note(note_id)
        category = category_repository.get_category(category_id)
        
        if not note or not category:
            return None
        
        # Initialize category_ids if it doesn't exist
        if "category_ids" not in note:
            note["category_ids"] = []
        elif not isinstance(note["category_ids"], list):
            note["category_ids"] = []
        
        # Check if already in category
        if category_id not in note["category_ids"]:
            # Add category to note
            note["category_ids"].append(category_id)
            return note_repository.update_note(note_id, {"category_ids": note["category_ids"]})
        
        return note
    
    def create_note(self, db, note_in: NoteCreate) -> Dict[str, Any]:
        """Create a new note"""
        # Create the note
        note = note_repository.create_note(note_in)
        
        # Add to vector store for semantic search
        if note:
            try:
                logger.info(f"Adding note {note['id']} to vector store")
                
                # Combine title and content for better embedding
                text_for_embedding = f"{note['title']} {note['content']}"
                
                # Create metadata for the document
                metadata = {
                    "title": note["title"],
                    "created_at": note.get("created_at", ""),
                    "category_ids": note.get("category_ids", [])
                }
                
                # Add to vector store
                success = vector_store.add_document(
                    doc_id=str(note["id"]),
                    text=text_for_embedding,
                    metadata=metadata
                )
                
                if success:
                    logger.info(f"Successfully added note {note['id']} to vector store")
                else:
                    logger.warning(f"Failed to add note {note['id']} to vector store")
            except Exception as e:
                logger.error(f"Error adding note to vector store: {str(e)}")
        
        return note
    
    def update_note(self, db, note_id: str, note_in: NoteUpdate) -> Optional[Dict[str, Any]]:
        """Update an existing note"""
        # Get the existing note
        db_note = note_repository.get_note(note_id)
        if not db_note:
            return None
        
        # Update the note
        note_data = note_in.dict(exclude_unset=True)
        updated_note = note_repository.update_note(note_id, note_data)
        
        # Update in vector store if content or title changed
        if updated_note and ("title" in note_data or "content" in note_data):
            # Combine title and content for better embedding
            text_for_embedding = f"{updated_note['title']} {updated_note['content']}"
            
            # Create metadata for the document
            metadata = {
                "title": updated_note["title"],
                "created_at": updated_note.get("created_at", ""),
                "category_ids": updated_note.get("category_ids", [])
            }
            
            # Update in vector store
            vector_store.update_document(
                doc_id=str(updated_note["id"]),
                text=text_for_embedding,
                metadata=metadata
            )
        
        return updated_note
    
    def delete_note(self, db, note_id: str) -> Optional[Dict[str, Any]]:
        """Delete a note"""
        note = note_repository.get_note(note_id)
        if not note:
            return None
        
        if note_repository.delete_note(note_id):
            # Remove from vector store
            vector_store.delete_document(str(note["id"]))
            return note
        return None
    
    def search_notes(self, db, query: NoteSearchQuery, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Search notes using semantic search for natural language queries or fallback to keyword search"""
        
        # If natural language query is provided, use semantic search
        if query.keyword:
            logger.info(f"Processing natural language query: {query.keyword}")
            
            # Check ChromaDB collection count
            try:
                collection_count = vector_store.collection.count()
                logger.info(f"ChromaDB collection has {collection_count} documents")
                
                if collection_count == 0:
                    logger.warning("No documents in ChromaDB collection - rebuilding index")
                    self.rebuild_vector_store(db, clear_existing=False)
                    collection_count = vector_store.collection.count()
                    logger.info(f"After rebuild, ChromaDB collection has {collection_count} documents")
            except Exception as e:
                logger.error(f"Error checking ChromaDB collection: {str(e)}")
            
            try:
                # Perform semantic search with vector embeddings
                logger.info("Performing semantic search with vector embeddings")
                semantic_results = vector_store.search(query.keyword, top_k=10)
                
                logger.info(f"Semantic search returned {len(semantic_results)} results")
                
                if semantic_results:
                    # Get full notes from repository using IDs from semantic search
                    note_ids = [doc['id'] for doc in semantic_results]
                    logger.info(f"Found note IDs: {note_ids}")
                    
                    notes = []
                    
                    for note_id in note_ids:
                        note = note_repository.get_note(note_id)
                        if note:
                            # Add similarity score
                            if semantic_results[0].get('similarity') is None:
                                note['_similarity'] = 1
                            else:
                                similarity = next((doc['similarity'] for doc in semantic_results if doc['id'] == note_id), 0)
                                note['_similarity'] = similarity
                            notes.append(note)
                        else:
                            logger.warning(f"Note with ID {note_id} found in vector store but not in database")
                    
                    logger.info(f"Retrieved {len(notes)} notes from database")
                    
                    # Sort by similarity score (descending)
                    notes.sort(key=lambda x: x.get('_similarity', 0), reverse=True)
                    
                    # Apply skip and limit for pagination
                    paginated_notes = notes[skip:skip+limit]
                    
                    return paginated_notes
                else:
                    logger.warning("No semantic results found")
                
                # If no semantic results were found, return empty list
                return []
            except Exception as e:
                logger.error(f"Error during semantic search: {str(e)}")
                return []
        
        # Fallback to basic keyword search if no natural language query
        if query.keyword:
            logger.info(f"Performing keyword search with keyword: {query.keyword}")
            return note_repository.search_notes(
                keyword=query.keyword,
                skip=skip, 
                limit=limit
            )
        
        # Return all notes if no search criteria provided
        logger.info("No search criteria provided, returning all notes")
        return note_repository.get_notes(skip=skip, limit=limit)
    
    
    def rebuild_vector_store(self, db, clear_existing: bool = False) -> int:
        """Rebuild the vector store with all notes in the database
        
        Args:
            db: Database connection
            clear_existing: If True, clear existing vector store before rebuilding
            
        Returns:
            Number of notes successfully added to the vector store
        """
        try:
            # Check if ChromaDB is accessible
            logger.info("Testing ChromaDB connection")
            initial_count = vector_store.collection.count()
            logger.info(f"Initial ChromaDB collection count: {initial_count}")
            
            # Clear existing entries if requested
            if clear_existing:
                logger.info("Clearing existing vector store before rebuilding")
                success = vector_store.clear_collection()
                logger.info(f"Clear collection {'succeeded' if success else 'failed'}")
                
                # Verify clear operation
                after_clear_count = vector_store.collection.count()
                logger.info(f"Collection count after clearing: {after_clear_count}")
            
            # Get all notes from database
            notes = note_repository.get_multi()
            count = 0
            
            logger.info(f"Rebuilding vector store with {len(notes)} notes")
            
            if not notes:
                logger.warning("No notes found in database to index")
                return 0
                
            # Process each note
            for i, note in enumerate(notes):
                try:
                    # Make sure we have required fields
                    if 'id' not in note or 'title' not in note or 'content' not in note:
                        logger.warning(f"Note {i} is missing required fields: {note.keys()}")
                        continue
                        
                    logger.info(f"Processing note {i+1}/{len(notes)}: {note['id']}")
                    
                    # Combine title and content for better embedding
                    text_for_embedding = f"{note['title']} {note['content']}"
                    
                    # Create metadata for the document
                    metadata = {
                        "title": note["title"],
                        "created_at": note.get("created_at", ""),
                        "updated_at": note.get("updated_at", ""),
                        "category_ids": note.get("category_ids", [])
                    }
                    
                    # Add to vector store
                    success = vector_store.add_document(
                        doc_id=str(note["id"]),
                        text=text_for_embedding,
                        metadata=metadata
                    )

                    if success:
                        count += 1
                        if count % 10 == 0:  # Log progress in batches
                            logger.info(f"Added {count}/{len(notes)} notes to vector store")
                    else:
                        logger.warning(f"Failed to add note {note['id']} to vector store")
                        
                except Exception as e:
                    logger.error(f"Error processing note {note.get('id', 'unknown')}: {str(e)}")
            
            # Verify final state
            final_count = vector_store.collection.count()
            logger.info(f"Vector store rebuild complete: {count}/{len(notes)} notes processed")
            logger.info(f"Final ChromaDB collection count: {final_count}")
            
            return count
            
        except Exception as e:
            logger.error(f"Error during vector store rebuild: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return 0


# Create instance for dependency injection
note_mongo_service = NoteMongoService()