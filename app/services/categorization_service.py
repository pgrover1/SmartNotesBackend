from typing import List, Dict, Any, Tuple, Optional
import re
import logging
from collections import Counter
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

class CategorizationService:
    """Service for automatic note categorization using OpenAI"""
    
    def __init__(self):
        """Initialize categorization service"""
        # Default categories
        self.default_categories = [
            "Project Management", 
            "Ideas/Brainstorming", 
            "Meeting Notes", 
            "Personal Tasks", 
            "Research", 
            "Customer Feedback",
            "Work",
            "Personal",
            "Study",
            "To-Do",
            "Health",
            "Finance"
        ]
        
        # Get API key from settings
        self.api_key = settings.OPENAI_API_KEY
        
        # Track if OpenAI is enabled
        self.openai_enabled = bool(self.api_key) and settings.ENABLE_AI_FEATURES
        
        if self.openai_enabled:
            # Initialize OpenAI client (updated for OpenAI v1.x API)
            self.client = OpenAI(api_key=self.api_key)
            logger.info("OpenAI service initialized successfully")
        else:
            self.client = None
            logger.warning("OpenAI API key not found. Note categorization will be limited.")
    
    def suggest_category(self, title: str, content: str) -> Dict[str, Any]:
        """Suggest a category for a note based on its title and content"""
        if not title and not content:
            return {
                "category": "Uncategorized",
                "confidence": 0.0,
                "keywords": [],
                "method": "default"
            }
        
        # Extract keywords from the text
        full_text = f"{title} {title} {content}"
        keywords = self.extract_keywords(full_text)
        
        # Use OpenAI for categorization
        if self.openai_enabled:
            try:
                category, confidence = self._openai_categorization(title, content)
                return {
                    "category": category,
                    "confidence": confidence,
                    "keywords": keywords,
                    "method": "openai"
                }
            except Exception as e:
                logger.error(f"Error using OpenAI for categorization: {str(e)}")
        
        # If OpenAI fails or is not enabled, return uncategorized
        return {
            "category": "Uncategorized",
            "confidence": 0.0,
            "keywords": keywords,
            "method": "default"
        }
    
    def _openai_categorization(self, title: str, content: str) -> Tuple[str, float]:
        """Use OpenAI to categorize notes"""
        # Construct the prompt for categorization
        prompt = f"""Categorize the following note into one of these categories: {', '.join(self.default_categories)}.
        
        Note Title: "{title}"
        Note Content: "{content}"
        
        Category:"""
        
        # Make API call to OpenAI (updated for OpenAI v1.x API)
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"You are a categorization assistant. Categorize the following note into exactly one of these categories: {', '.join(self.default_categories)}."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            n=1,
            temperature=0.2,  # Lower temperature for more focused results
        )
        
        # Extract the predicted category
        predicted_category = response.choices[0].message.content.strip()
        
        # Clean up the category (sometimes the model might include quotes or extra text)
        for category in self.default_categories:
            if category.lower() in predicted_category.lower():
                predicted_category = category
                break
        
        # Use the model's choice as the category and assign a high confidence
        return predicted_category, 0.9
    
    def extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """Extract the most relevant keywords from text"""
        if not text:
            return []
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove common stop words
        stop_words = [
            "the", "and", "a", "to", "of", "in", "is", "it", "you", "that",
            "he", "was", "for", "on", "are", "with", "as", "his", "they",
            "at", "be", "this", "have", "from", "or", "had", "by", "but",
            "not", "what", "all", "were", "we", "when", "your", "can", "said",
            "there", "use", "an", "each", "which", "she", "do", "how", "their",
            "if", "will", "up", "other", "about", "out", "many", "then", "them",
            "these", "so", "some", "her", "would", "make", "like", "him", "into",
            "time", "has", "look", "two", "more", "go", "see", "no", "way", "could",
            "people", "my", "than", "first", "been", "call", "who", "its", "now",
            "find", "long", "down", "day", "did", "get", "come", "made", "may", "part"
        ]
        
        # Tokenize and clean words
        words = re.findall(r'\b\w+\b', text)
        words = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Count word frequencies
        word_counts = Counter(words)
        
        # Return most common words
        return [word for word, _ in word_counts.most_common(max_keywords)]


# Create instance for dependency injection
categorization_service = CategorizationService()