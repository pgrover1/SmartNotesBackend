from typing import Dict, Any, Optional
import logging
import json
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

class NoteAnalysisService:
    """Service for AI-powered note analysis (summarization and sentiment analysis)"""
    
    def __init__(self):
        """Initialize note analysis service"""
        # Get API key from settings
        self.api_key = settings.OPENAI_API_KEY
        
        # Track if OpenAI is enabled
        self.openai_enabled = bool(self.api_key) and settings.ENABLE_AI_FEATURES
        
        # Sentiment categories
        self.sentiment_categories = ["Positive", "Neutral", "Negative","Mixed"]
        
        if self.openai_enabled:
            # Initialize OpenAI client (updated for OpenAI v1.x API)
            self.client = OpenAI(api_key=self.api_key)
            logger.info("OpenAI service initialized for note analysis")
        else:
            self.client = None
            logger.warning("OpenAI API key not found. Note analysis will be limited.")
    
    def analyze_note(self, title: str, content: str) -> Dict[str, Any]:
        """Analyze a note to generate summary and sentiment"""
        # Default response when OpenAI is not available
        result = {
            "summary": None,
            "sentiment": "Neutral",
            "analysis_method": "none"
        }
        
        # Skip analysis for empty content
        if not content or len(content) < 20:
            return result
        
        # Use OpenAI for analysis
        if self.openai_enabled:
            try:
                # Get sentiment analysis
                result["sentiment"] = self.analyze_sentiment(content)
                result["analysis_method"] = "openai"
                
                return result
            except Exception as e:
                logger.error(f"Error using OpenAI for note analysis: {str(e)}")
        
        return result
    def analyze_sentiment(self, content: str) -> str:
        """Analyze the sentiment of the note content"""
        if not self.openai_enabled:
            return "Neutral"
            
        # Create prompt for sentiment analysis
        prompt = f"""Analyze the sentiment of the following text and classify it as exactly one of: Positive, Neutral, Mixed or Negative.
        
        Text: "{content}"
        
        Sentiment:"""
        
        try:
            # Make API call to OpenAI with GPT-4o (updated for OpenAI v1.x API)
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a sentiment analysis assistant. Classify text as Positive, Neutral, or Negative only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                n=1,
                temperature=0.1
            )
            
            # Extract the sentiment from ChatCompletion response
            sentiment = response.choices[0].message.content.strip()
            
            # Ensure sentiment is one of the valid categories
            for category in self.sentiment_categories:
                if category.lower() in sentiment.lower():
                    return category
            
            # Default to Neutral if the response is unexpected
            return "Neutral"
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return "Neutral"
    
    def generate_openai_summary(self, title: str, content: str, max_length: int = 150, model: str = "gpt-4o") -> Dict[str, Any]:
        """Generate an OpenAI-powered summary with customizable length and model"""
        result = {
            "summary": None,
            "success": False,
            "error": None,
            "model_used": model
        }
        
        if not content:
            result["error"] = "No content provided"
            return result
            
        # Count words in the content
        word_count = len(content.split())
        
        # Only summarize content that's more than 200 words
        if word_count < 20:
            result["error"] = "Content is less than 200 words and doesn't need summarization"
            return result
            
        if not self.openai_enabled:
            result["error"] = "OpenAI API key not configured"
            return result
        
        # Validate model
        if model not in ["gpt-4o", "gpt-3.5-turbo"]:
            model = "gpt-4o"  # Default to GPT-4o if invalid model specified
        
        try:
            # Construct the prompt for customized summarization
            prompt = f"""Summarize the following note in a concise way. Keep the summary under {max_length} characters:
            
            Note Title: "{title}"
            Note Content: "{content}"
            
            Summary:"""
            
            # Make API call to OpenAI with specified model (updated for OpenAI v1.x API)
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant that summarizes text concisely and accurately."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max(100, max_length // 3),  # Estimate tokens based on characters
                n=1,
                temperature=0.3
            )
            
            # Extract and return the summary from ChatCompletion response
            summary = response.choices[0].message.content.strip()
            result["summary"] = summary
            result["success"] = True
            return result
        except Exception as e:
            logger.error(f"Error generating OpenAI summary: {str(e)}")
            result["error"] = str(e)
            return result


# Create instance for dependency injection
note_analysis_service = NoteAnalysisService()