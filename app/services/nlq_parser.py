import json
from typing import Dict, Any, List, Optional
import logging
import numpy as np
from openai import OpenAI
from app.core.config import settings
from datetime import date
logger = logging.getLogger(__name__)

class NLQParserService:
    """Service for handling natural language queries using OpenAI embeddings"""
    
    def __init__(self):
        """Initialize the NLQ service with OpenAI client"""
        # Get API key from settings
        self.api_key = settings.OPENAI_API_KEY
        
        # Track if OpenAI is enabled
        self.openai_enabled = bool(self.api_key) and settings.ENABLE_AI_FEATURES
        
        if self.openai_enabled:
            # Initialize OpenAI client
            self.client = OpenAI(api_key=self.api_key)
            logger.info("OpenAI service initialized for NLQ parsing")
            self.embedding_model = "text-embedding-3-small"
        else:
            self.client = None
            logger.warning("OpenAI API key not found. NLQ features will be limited.")
    
    def create_embedding(self, text: str) -> List[float]:
        """Create an embedding vector for text using OpenAI's embedding API"""
        if not self.openai_enabled or not self.client:
            logger.warning("OpenAI is not enabled, cannot create embeddings")
            return []
        
        if not text or not text.strip():
            logger.warning("Cannot create embedding for empty text")
            return []
            
        try:
            logger.info(f"Creating embedding using model: {self.embedding_model}")
            logger.info(f"Text length: {len(text)} characters")
            
            # Truncate text if too long (OpenAI has token limits)
            max_chars = 8000  # Approximate safe limit
            if len(text) > max_chars:
                logger.warning(f"Text too long ({len(text)} chars), truncating to {max_chars} chars")
                text = text[:max_chars]
            
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text,
                encoding_format="float"
            )
            
            embedding = response.data[0].embedding
            logger.info(f"Successfully created embedding of dimension {len(embedding)}")
            
            return embedding
        except Exception as e:
            logger.error(f"Error creating embedding: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Compute cosine similarity between two embeddings"""
        if not embedding1 or not embedding2:
            return 0
            
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Compute cosine similarity
            similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
            return float(similarity)
        except Exception as e:
            logger.error(f"Error computing similarity: {str(e)}")
            return 0
        
    def parse_query_intent(self, query: str) -> Dict:
        """Parse natural language query to extract intent and filters"""
        if not self.openai_enabled or not self.client:
            logger.warning("OpenAI is not enabled, using basic query parsing")
            return {"type": "keyword", "query": query, "filters": {}}
        
        try:
            # Define the prompt for the LLM
            system_prompt = """
            You are a query parser for a note-taking app. Extract the query type and any filters from the user's query.
            Output JSON with these fields:
            - type: "list_all", "keyword", "temporal", "category", or "combined"
            - search_terms: keywords for semantic search (empty string if none)
            - filters: object with filter criteria (date, category, etc.)
            """
            
            # Call the OpenAI API for parsing
            completion = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Parse this query: {query}"}
                ],
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            parsed_query = json.loads(completion.choices[0].message.content)
            logger.info(f"Parsed query: {parsed_query}")
            return parsed_query
            
        except Exception as e:
            logger.error(f"Error parsing query intent: {str(e)}")
            return {"type": "keyword", "query": query, "filters": {}}
        
    def get_temporal_date(self, query: str) -> Dict:
        """Parse natural language query to extract intent and filters"""
        if not self.openai_enabled or not self.client:
            logger.warning("OpenAI is not enabled, using basic query parsing")
            return {"type": "keyword", "query": query, "filters": {}}
        
        try:
            now = date.today()
            # Define the prompt for the LLM
            system_prompt = f"""
            your job is to tell the from date and to date based on the user request like if user ask give me notes then give me start_date = {now} -1 and last_date= {now} -1.
            If user will ask to give notes for last week then give me start_date = {now.strftime("%Y-%m-%d")} -7 and last_date= {now}.
            Output JSON with these fields:
            - Response: both "start_date", "end_date" in date format "
            """
            
            # Call the OpenAI API for parsing
            completion = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Parse this query: {query}"}
                ],
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            parsed_query = json.loads(completion.choices[0].message.content)
            logger.info(f"Parsed query: {parsed_query}")
            return parsed_query
            
        except Exception as e:
            logger.error(f"Error parsing query intent: {str(e)}")
            return {"type": "keyword", "query": query, "filters": {}}

    def rank_documents(self, query_embedding: List[float], document_embeddings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank documents by similarity to the query embedding"""
        if not query_embedding:
            return []
            
        try:
            # Compute similarity for each document
            for doc in document_embeddings:
                doc["similarity"] = self.compute_similarity(query_embedding, doc["embedding"])
            
            # Sort by similarity (descending)
            ranked_docs = sorted(document_embeddings, key=lambda x: x["similarity"], reverse=True)
            return ranked_docs
        except Exception as e:
            logger.error(f"Error ranking documents: {str(e)}")
            return []


# Create instance for dependency injection
nlq_parser_service = NLQParserService()