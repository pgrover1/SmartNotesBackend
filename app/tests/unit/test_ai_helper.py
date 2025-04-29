"""Helper utilities for mocking AI services in tests"""
import pytest
from unittest.mock import MagicMock, patch

class MockAIServices:
    """Mock AI services for testing"""
    
    @staticmethod
    def create_mock_ai_service():
        """Create a mock AIService instance"""
        mock_ai = MagicMock()
        
        # Configure sentiment analysis mock
        mock_ai.analyze_sentiment.return_value = "Positive"
        
        # Configure summarization mock
        
        # Configure NLQ processing mock
        mock_ai.process_natural_language_query.return_value = {
            "keyword": "Work",
            "category_id": None
        }
        
        # Configure category suggestion mock
        mock_ai.suggest_category.return_value = "Work"
        
        return mock_ai
    
    @staticmethod
    def create_mock_ai_factory():
        """Create a mock for the factory_ai.get_ai_services function"""
        # Create individual mock services
        mock_categorization = MagicMock()
        mock_categorization.suggest_category.return_value = {
            "category": "Work",
            "confidence": 0.9,
            "keywords": ["meeting", "work", "notes"],
            "method": "openai"
        }
        
        mock_note_analysis = MagicMock()
        mock_note_analysis.generate_openai_summary.return_value = {
            "summary": "A test note summary",
            "success": True,
            "error": None,
            "model_used": "gpt-4o"
        }
        mock_note_analysis.analyze_sentiment.return_value = "Positive"
        mock_note_analysis.analyze_note.return_value = {
            "sentiment": "Positive",
            "keywords": ["work", "meeting", "project"],
            "entities": ["Meeting", "Project"],
            "summary": "This is a summary of the note"
        }
        
        # Return dictionary of services
        return {
            "categorization": mock_categorization,
            "note_analysis": mock_note_analysis
        }

@pytest.fixture
def mock_ai_service():
    """Fixture that returns a mock AIService instance"""
    return MockAIServices.create_mock_ai_service()

@pytest.fixture
def mock_ai_factory():
    """Fixture that patches factory_ai.get_ai_services"""
    with patch('app.services.factory_ai.get_ai_services', 
              return_value=MockAIServices.create_mock_ai_factory()) as mock:
        yield mock