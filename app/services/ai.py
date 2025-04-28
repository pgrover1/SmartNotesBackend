from typing import List, Dict, Any, Tuple, Optional
import logging
import os
import re
from datetime import datetime, timedelta

from app.core.config import settings

# Optional import for AI models
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
    from transformers import AutoModelForSequenceClassification
    import torch
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    HAS_AI_DEPS = True
except ImportError:
    HAS_AI_DEPS = False

# Configure logging
logger = logging.getLogger(__name__)

class AIService:
    """Service for AI-powered features"""
    
    def __init__(self):
        """Initialize AI models if enabled"""
        self.is_enabled = settings.ENABLE_AI_FEATURES and HAS_AI_DEPS
        self.models = {}
        
        if self.is_enabled:
            try:
                # Initialize models
                self._init_summarization_model()
                self._init_sentiment_model()
                self._init_embeddings_model()
                self._init_zero_shot_model()
                
                logger.info("AI models initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize AI models: {str(e)}")
                self.is_enabled = False
        else:
            logger.warning("AI features are disabled or dependencies not installed")
    
    def _init_summarization_model(self):
        """Initialize summarization model"""
        if self.is_enabled:
            try:
                # Use a small, efficient model for summarization
                model_name = "facebook/bart-large-cnn"
                self.models["summarizer"] = pipeline(
                    "summarization", 
                    model=model_name,
                    device=0 if torch.cuda.is_available() else -1
                )
                logger.info(f"Summarization model loaded: {model_name}")
            except Exception as e:
                logger.error(f"Failed to load summarization model: {str(e)}")
    
    def _init_sentiment_model(self):
        """Initialize sentiment analysis model"""
        if self.is_enabled:
            try:
                # Use a small, efficient model for sentiment
                model_name = "distilbert-base-uncased-finetuned-sst-2-english"
                self.models["sentiment"] = pipeline(
                    "sentiment-analysis", 
                    model=model_name,
                    device=0 if torch.cuda.is_available() else -1
                )
                logger.info(f"Sentiment model loaded: {model_name}")
            except Exception as e:
                logger.error(f"Failed to load sentiment model: {str(e)}")
    
    def _init_embeddings_model(self):
        """Initialize embeddings model for semantic similarity"""
        if self.is_enabled:
            try:
                # Use a small, efficient model for embeddings
                model_name = "sentence-transformers/all-MiniLM-L6-v2"
                self.models["embeddings"] = pipeline(
                    "feature-extraction", 
                    model=model_name,
                    device=0 if torch.cuda.is_available() else -1
                )
                logger.info(f"Embeddings model loaded: {model_name}")
            except Exception as e:
                logger.error(f"Failed to load embeddings model: {str(e)}")
    
    def _init_zero_shot_model(self):
        """Initialize zero-shot classification model for category suggestion"""
        if self.is_enabled:
            try:
                # Use a model that's good at zero-shot classification
                model_name = "facebook/bart-large-mnli"
                self.models["zero_shot"] = pipeline(
                    "zero-shot-classification",
                    model=model_name,
                    device=0 if torch.cuda.is_available() else -1
                )
                logger.info(f"Zero-shot classification model loaded: {model_name}")
            except Exception as e:
                logger.error(f"Failed to load zero-shot classification model: {str(e)}")
    
    def generate_summary(self, text: str) -> str:
        """Generate a summary for longer text"""
        if not self.is_enabled or "summarizer" not in self.models:
            # Fallback: Return first 100 characters + "..."
            return text[:100] + "..." if len(text) > 100 else text
        
        try:
            # Handle text length limitations
            max_input_length = 1024
            if len(text) > max_input_length:
                text = text[:max_input_length]
                
            # Generate summary
            summary = self.models["summarizer"](
                text, 
                max_length=100, 
                min_length=30, 
                do_sample=False
            )
            return summary[0]["summary_text"]
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            # Fallback
            return text[:100] + "..." if len(text) > 100 else text
    
    def analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment of text"""
        if not self.is_enabled or "sentiment" not in self.models:
            return "Neutral"  # Default fallback
        
        try:
            # Truncate long text to prevent token limitation issues
            max_input_length = 512
            if len(text) > max_input_length:
                text = text[:max_input_length]
                
            # Get sentiment prediction
            result = self.models["sentiment"](text)
            label = result[0]["label"]
            score = result[0]["score"]
            
            # Map POSITIVE/NEGATIVE to Positive/Negative/Neutral
            # Use "Neutral" for less confident predictions
            if score < 0.65:  # Confidence threshold
                return "Neutral"
                
            sentiment_map = {
                "POSITIVE": "Positive",
                "NEGATIVE": "Negative"
            }
            return sentiment_map.get(label, "Neutral")
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return "Neutral"  # Default fallback
    
    def suggest_category(self, text: str, categories: List[Tuple[int, str]]) -> Optional[int]:
        """Suggest category ID based on text content and available categories"""
        # Try using zero-shot classification first (more accurate)
        if self.is_enabled and "zero_shot" in self.models and categories:
            try:
                # Extract category IDs and names
                category_ids = [c[0] for c in categories]
                category_names = [c[1] for c in categories]
                
                # Use zero-shot classification to find the best category
                result = self.models["zero_shot"](
                    text, 
                    candidate_labels=category_names,
                    hypothesis_template="This text is about {}."
                )
                
                # Get the highest scoring category
                best_match_idx = 0
                best_score = result['scores'][0]
                
                # Only suggest if confidence is high enough
                if best_score > 0.45:  # Confidence threshold
                    # Map back to category ID
                    return category_ids[best_match_idx]
                return None
                
            except Exception as e:
                logger.error(f"Error in zero-shot classification: {str(e)}")
                # Fall back to embedding similarity approach
                pass
        
        # Fallback to embedding similarity approach
        if self.is_enabled and "embeddings" in self.models and categories:
            try:
                # Extract category IDs and names
                category_ids = [c[0] for c in categories]
                category_names = [c[1] for c in categories]
                
                # Get embedding for text
                text_embedding = self.models["embeddings"](text)
                text_embedding = np.mean(text_embedding[0], axis=0).reshape(1, -1)
                
                # Get embeddings for categories
                category_embeddings = []
                for category_name in category_names:
                    embedding = self.models["embeddings"](category_name)
                    embedding = np.mean(embedding[0], axis=0).reshape(1, -1)
                    category_embeddings.append(embedding)
                
                # Compute similarity
                similarities = []
                for embedding in category_embeddings:
                    similarity = cosine_similarity(text_embedding, embedding)[0][0]
                    similarities.append(similarity)
                
                # Find most similar category
                max_idx = np.argmax(similarities)
                max_sim = similarities[max_idx]
                
                # Only suggest if similarity is above threshold
                if max_sim > 0.35:  # Slightly increased threshold
                    return category_ids[max_idx]
                return None
            except Exception as e:
                logger.error(f"Error suggesting category: {str(e)}")
                return None
        
        return None  # Fall back to no suggestion
    
    def process_natural_language_query(self, query: str) -> Dict[str, Any]:
        """Process natural language query into structured search parameters"""
        result = {
            "keyword": None,
            "category_id": None
        }
        
        # Simple rule-based NLQ processing (could be enhanced with ML)
        
        # Extract potential category mentions
        category_match = re.search(r"in\s+(?:the\s+)?(?:category\s+)?['\"]?([\w\s]+)['\"]?", query, re.IGNORECASE)
        if category_match:
            # Note: We're just extracting the category name here
            # In a real implementation, you'd look up the category ID in the DB
            category_name = category_match.group(1).strip()
            # Set as keyword since we can't look up DB here
            result["keyword"] = category_name
        
        # Extract date references
        date_patterns = [
            # "from last Monday"
            (r"from\s+last\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)", 7),
            # "from yesterday"
            (r"from\s+yesterday", 1),
            # "from last week"
            (r"from\s+last\s+week", 7),
            # "from last month"
            (r"from\s+last\s+month", 30),
        ]
        
        for pattern, days_ago in date_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                # Here we would typically convert this to a date range filter
                # For now, just extract key terms from the query
                pass
        
        # Use advanced NLP if available
        if self.is_enabled and "embeddings" in self.models:
            try:
                # Remove common words and extract the most likely search terms
                stop_words = ["find", "my", "the", "from", "about", "with", "where", "when", "notes", "note", 
                             "show", "get", "give", "want", "need", "have", "has", "had", "was", "were", "will"]
                words = query.lower().split()
                keywords = [word for word in words if word not in stop_words and len(word) > 3]
                
                if keywords:
                    # Use the most relevant keywords
                    result["keyword"] = " ".join(keywords[:3])
                
                return result
            except Exception as e:
                logger.error(f"Error in NLP query processing: {str(e)}")
                # Fall back to simple rule-based extraction
        
        # Simple fallback extraction
        stop_words = ["find", "my", "the", "from", "about", "with", "where", "when", "notes", "note"]
        words = query.lower().split()
        keywords = [word for word in words if word not in stop_words and len(word) > 3]
        
        if keywords:
            # Use the most relevant keywords
            result["keyword"] = " ".join(keywords[:3])
        
        return result

# Create instance for dependency injection
ai_service = AIService()
