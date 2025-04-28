import pytest
from unittest.mock import patch, MagicMock

from app.services.ai import AIService

# Test AIService functionality

def test_sentiment_analysis_fallback():
    """Test sentiment analysis fallback when AI is disabled"""
    # Create an AI service with is_enabled set to False
    ai_service = AIService()
    ai_service.is_enabled = False
    
    # Test the fallback behavior
    result = ai_service.analyze_sentiment("This is a positive text")
    assert result == "Neutral"

def test_summarization_fallback():
    """Test summarization fallback when AI is disabled"""
    # Create an AI service with is_enabled set to False
    ai_service = AIService()
    ai_service.is_enabled = False
    
    # Test the fallback behavior for short text
    short_text = "This is a short text"
    result = ai_service.generate_summary(short_text)
    assert result == short_text
    
    # Test the fallback behavior for long text
    long_text = "This is a very long text that should be truncated" + " words" * 50
    result = ai_service.generate_summary(long_text)
    assert result == long_text[:100] + "..."

def test_natural_language_query_processing():
    """Test NLQ processing functionality"""
    with patch('app.services.ai.HAS_AI_DEPS', False):
        ai_service = AIService()
        ai_service.is_enabled = False
        
        # Test category extraction
        result = ai_service.process_natural_language_query("Find notes in the work category")
        assert result["keyword"] == "work category"
        
        # Test keyword extraction after stopword removal
        result = ai_service.process_natural_language_query("Find my notes about programming")
        assert result["keyword"] == "programming"
        
        # Test with multiple keywords
        result = ai_service.process_natural_language_query("Find my notes about Python programming language")
        assert "python programming language" in result["keyword"]