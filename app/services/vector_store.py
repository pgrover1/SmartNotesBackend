from typing import Dict, Any, List, Optional
import logging
import os
import json
from datetime import datetime
import chromadb
from chromadb.config import Settings
from app.services.nlq_parser import nlq_parser_service
from app.core.config import settings as app_settings

logger = logging.getLogger(__name__)

class ChromaDBVectorStore:
    """Vector store implementation using ChromaDB for semantic search"""
    
    def __init__(self):
        """Initialize the ChromaDB vector store"""
        # Set up data directory
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../data/chroma')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize ChromaDB client
        try:
            self.client = chromadb.PersistentClient(
                path=self.data_dir,
                settings=Settings(
                    anonymized_telemetry=False
                )
            )
            
            # Create or get the collection for notes
            self.collection = self.client.get_or_create_collection(
                name="notes",
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity
            )
            
            logger.info(f"ChromaDB initialized with {self.collection.count()} documents")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {str(e)}")
            raise
    
    def add_document(self, doc_id: str, text: str, metadata: Dict[str, Any] = None) -> bool:
        """Add a document to the vector store"""
        try:
            # Create embedding using OpenAI
            embedding = nlq_parser_service.create_embedding(text)
            
            if not embedding:
                logger.warning(f"Failed to create embedding for document {doc_id}")
                return False
            
            # Prepare metadata (ensure all values are strings for ChromaDB)
            string_metadata = {}
            if metadata:
                for k, v in metadata.items():
                    if isinstance(v, list):
                        string_metadata[k] = json.dumps(v)
                    elif isinstance(v, dict):
                        string_metadata[k] = json.dumps(v)
                    else:
                        string_metadata[k] = str(v)
            
            # Add timestamp
            string_metadata["timestamp"] = datetime.now().isoformat()
            
            # Check if document exists and update it
            try:
                self.collection.get(ids=[doc_id])
                existing_doc = self.collection.get(ids=[doc_id])
                if existing_doc and existing_doc["ids"]:
                    # Document exists, update it
                    logger.info(f"Document {doc_id} exists, updating it")
                    self.collection.update(
                        ids=[doc_id],
                        embeddings=[embedding],
                        metadatas=[string_metadata],
                        documents=[text]
                    )
                    logger.info(f"Updated document {doc_id} in ChromaDB")
                else:
                    # Document doesn't exist, add it
                    logger.info(f"Document {doc_id} does not exist, creating it")
                    self.collection.add(
                        ids=[doc_id],
                        embeddings=[embedding],
                        metadatas=[string_metadata],
                        documents=[text]
                    )
                    logger.info(f"Added document {doc_id} to ChromaDB")
                
                print(f"Updated document self.collection.count() {self.collection.count()} in ChromaDB")
                logger.info(f"Updated document self.collection.count() {self.collection.count()} in ChromaDB")
                 
            except Exception:
                # Document doesn't exist, add it
                self.collection.add(
                    ids=[doc_id],
                    embeddings=[embedding],
                    metadatas=[string_metadata],
                    documents=[text]
                )
                
            logger.info(f"Added/updated document {doc_id} in ChromaDB")
            return True
            
        except Exception as e:
            logger.error(f"Error adding document to ChromaDB: {str(e)}")
            return False
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the vector store"""
        try:
            self.collection.delete(ids=[doc_id])
            logger.info(f"Deleted document {doc_id} from ChromaDB")
            return True
        except Exception as e:
            logger.error(f"Error deleting document from ChromaDB: {str(e)}")
            return False
    
    def update_document(self, doc_id: str, text: str, metadata: Dict[str, Any] = None) -> bool:
        """Update a document in the vector store"""
        return self.add_document(doc_id, text, metadata)
        
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Enhanced search that handles different types of queries"""
        
        # Parse the query intent
        parsed_query = nlq_parser_service.parse_query_intent(query)
        query_type = parsed_query.get("type", "keyword")
        search_terms = parsed_query.get("search_terms", "")
        filters = parsed_query.get("filters", {})
        
        # Handle different query types
        if query_type == "list_all":
            # Return all notes (with pagination)
            return self._get_all_notes(limit=top_k)
            
        elif query_type == "temporal":
            # Handle date-based filtering
            date_result = nlq_parser_service.get_temporal_date(query)
            response_data = date_result.get("Response", {})
            start_date = response_data.get("start_date")
            end_date = response_data.get("end_date")


            return self._filter_by_date(start_date,end_date, search_terms, top_k)
            
        else:
            # Default to vector search with the original or modified query
            search_query = search_terms if search_terms else query
            return self.search_old(search_query, top_k)
    
    def _get_all_notes(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Retrieve all notes from the collection with pagination"""
        try:
            # Get all document IDs from the collection
            all_ids = self.collection.get(include=[])["ids"]
            
            # Apply pagination
            paginated_ids = all_ids[offset:offset+limit] if all_ids else []
            
            if not paginated_ids:
                logger.info("No notes found in the collection")
                return []
                
            # Get the actual documents with metadata
            results = self.collection.get(
                ids=paginated_ids,
                include=["metadatas", "documents"]
            )
            
            # Format the results
            formatted_results = []
            for i, doc_id in enumerate(results["ids"]):
                formatted_results.append({
                    "id": doc_id,
                    "metadata": results["metadatas"][i],
                    "content": results["documents"][i]
                })
                
            logger.info(f"Retrieved {len(formatted_results)} notes of {len(all_ids)} total")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error retrieving all notes: {str(e)}")
            return []
        
    def _filter_by_date(self, start_date: str, end_date: str, search_terms: str = "", limit: int = 5) -> List[Dict[str, Any]]:
        """Filter notes by date criteria"""
        try:
            # Extract date filters
            # Convert to actual date objects if provided as strings
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                
                
            # Query with date filter
            where_clause = {}
            if start_date:
                where_clause["created_at"] = {"$gt": start_date.isoformat()}
            if end_date:
                if "created_at" not in where_clause:
                    where_clause["created_at"] = {}
                where_clause["created_at"]["$lte"] = end_date.isoformat()
                
            # Get results with the where clause
            if search_terms:
                # Combine semantic search with date filtering
                embedding = nlq_parser_service.create_embedding(search_terms)
                results = self.collection.query(
                    query_embeddings=[embedding],
                    where=where_clause,
                    n_results=limit
                )
            else:
                # Just filter by date
                results = self.collection.get(
                    where=where_clause,
                    limit=limit,
                    include=["metadatas", "documents"]
                )
                
            # Format the results
            formatted_results = []
            for i, doc_id in enumerate(results["ids"]):
                formatted_results.append({
                    "id": doc_id,
                    "metadata": results["metadatas"][i] if "metadatas" in results else {},
                    "content": results["documents"][i] if "documents" in results else ""
                })
                
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error filtering by date: {str(e)}")
            return []
        
    def search_old(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for documents similar to the query"""
        try:
            # Check if collection is empty
            if self.collection.count() == 0:
                logger.warning("ChromaDB collection is empty, no documents to search")
                return []
            
            # Create embedding for the query
            logger.info(f"Creating embedding for query: {query}")
            embedding = nlq_parser_service.create_embedding(query)
            
            if not embedding:
                logger.warning("Failed to create embedding for query")
                return []
            
            logger.info(f"Embedding created, length: {len(embedding)}")
            
            # Search ChromaDB
            logger.info(f"Searching ChromaDB for top {top_k} results")
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=min(top_k, self.collection.count()),
                include=["documents", "metadatas", "distances"]
            )
            
            # Log raw results for debugging
            logger.info(f"ChromaDB results structure: {list(results.keys())}")
            
            if "ids" in results:
                logger.info(f"Number of result clusters: {len(results['ids'])}")
                if len(results["ids"]) > 0:
                    logger.info(f"Number of results in first cluster: {len(results['ids'][0])}")
            
            # Format results to match expected output
            formatted_results = []
            
            if results.get("ids") and len(results["ids"]) > 0 and len(results["ids"][0]) > 0:
                logger.info(f"Found {len(results['ids'][0])} documents")
                
                similarity_threshold = 0.7 

                for i, doc_id in enumerate(results["ids"][0]):
                    distance = results["distances"][0][i] if "distances" in results else 0
                    similarity = 1 - (distance / 2)

                    logger.info(f"Document {i}: id={doc_id}, distance={distance}, similarity={similarity}")

                    if similarity >= similarity_threshold:
                        # Parse metadata (as before)
                        metadata = results["metadatas"][0][i] if "metadatas" in results and len(results["metadatas"]) > 0 else {}
                        parsed_metadata = {}
                        for k, v in metadata.items():
                            try:
                                parsed_metadata[k] = json.loads(v)
                            except Exception:
                                parsed_metadata[k] = v

                        formatted_results.append({
                            "id": doc_id,
                            "text": results["documents"][0][i] if "documents" in results and len(results["documents"]) > 0 else "",
                            "metadata": parsed_metadata,
                            "similarity": similarity
                        })
                    else:
                        logger.info(f"Document {doc_id} below similarity threshold ({similarity:.2f} < {similarity_threshold})")
            else:
                logger.warning("ChromaDB returned no results or empty structure")
            
            logger.info(f"Returning {len(formatted_results)} formatted results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching in ChromaDB: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def clear_collection(self) -> bool:
        """Clear all documents from the collection"""
        try:
            # Get all document IDs
            all_ids = self.collection.get()["ids"]
            
            # Delete all documents
            if all_ids:
                self.collection.delete(ids=all_ids)
                
            logger.info(f"Cleared ChromaDB collection, removed {len(all_ids)} documents")
            return True
        except Exception as e:
            logger.error(f"Error clearing ChromaDB collection: {str(e)}")
            return False


# Create instance for dependency injection
vector_store = ChromaDBVectorStore()