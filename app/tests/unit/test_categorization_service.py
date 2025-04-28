import pytest
from unittest.mock import MagicMock, patch

from app.services.categorization import CategorizationService

class TestCategorizationService:
    """Tests for the CategorizationService"""
    
    def test_init_with_openai_enabled(self):
        """Test initialization when OpenAI is enabled"""
        with patch('app.services.categorization_service.settings') as mock_settings, \
             patch('app.services.categorization_service.OpenAI') as mock_openai:
            
            # Configure mock settings
            mock_settings.OPENAI_API_KEY = "test-api-key"
            mock_settings.ENABLE_AI_FEATURES = True
            
            # Create service
            service = CategorizationService()
            
            # Verify client was initialized
            assert service.openai_enabled is True
            mock_openai.assert_called_once_with(api_key="test-api-key")
    
    def test_init_with_openai_disabled(self):
        """Test initialization when OpenAI is disabled"""
        with patch('app.services.categorization_service.settings') as mock_settings, \
             patch('app.services.categorization_service.OpenAI') as mock_openai:
            
            # Configure mock settings with no API key
            mock_settings.OPENAI_API_KEY = ""
            mock_settings.ENABLE_AI_FEATURES = True
            
            # Create service
            service = CategorizationService()
            
            # Verify client was not initialized
            assert service.openai_enabled is False
            mock_openai.assert_not_called()
    
    def test_suggest_category_with_empty_input(self):
        """Test suggest_category with empty title and content"""
        # Create service
        service = CategorizationService()
        
        # Call suggest_category with empty input
        result = service.suggest_category("", "")
        
        # Verify default response
        assert result["category"] == "Uncategorized"
        assert result["confidence"] == 0.0
        assert result["keywords"] == []
        assert result["method"] == "default"
    
    def test_suggest_category_with_openai_disabled(self):
        """Test suggest_category when OpenAI is disabled"""
        # Create service with OpenAI disabled
        service = CategorizationService()
        service.openai_enabled = False
        
        # Call suggest_category
        result = service.suggest_category("Work Meeting", "Notes from today's project meeting")
        
        # Verify default response with extracted keywords
        assert result["category"] == "Uncategorized"
        assert result["confidence"] == 0.0
        assert len(result["keywords"]) > 0
        assert "meeting" in result["keywords"] or "project" in result["keywords"]
        assert result["method"] == "default"
    
    def test_suggest_category_with_openai_enabled(self):
        """Test suggest_category when OpenAI is enabled"""
        # Create service with mocked OpenAI client
        service = CategorizationService()
        service.openai_enabled = True
        
        # Mock _openai_categorization
        with patch.object(service, '_openai_categorization', return_value=("Work", 0.9)):
            
            # Call suggest_category
            result = service.suggest_category("Work Meeting", "Notes from today's project meeting")
            
            # Verify OpenAI response
            assert result["category"] == "Work"
            assert result["confidence"] == 0.9
            assert len(result["keywords"]) > 0
            assert result["method"] == "openai"
    
    def test_suggest_category_with_openai_error(self):
        """Test suggest_category when OpenAI throws an error"""
        # Create service with mocked OpenAI client
        service = CategorizationService()
        service.openai_enabled = True
        
        # Mock _openai_categorization to raise exception
        with patch.object(service, '_openai_categorization', side_effect=Exception("API error")):
            
            # Call suggest_category
            result = service.suggest_category("Work Meeting", "Notes from today's project meeting")
            
            # Verify default response with extracted keywords
            assert result["category"] == "Uncategorized"
            assert result["confidence"] == 0.0
            assert len(result["keywords"]) > 0
            assert result["method"] == "default"
    
    def test_openai_categorization(self):
        """Test _openai_categorization method"""
        # Create service with mocked OpenAI client
        service = CategorizationService()
        service.openai_enabled = True
        
        # Mock OpenAI client response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Meeting Notes"
        
        service.client = MagicMock()
        service.client.chat.completions.create.return_value = mock_response
        
        # Call _openai_categorization
        category, confidence = service._openai_categorization("Team Meeting", "Notes from our weekly team meeting")
        
        # Verify OpenAI was called with correct parameters
        service.client.chat.completions.create.assert_called_once()
        call_args = service.client.chat.completions.create.call_args[1]
        assert call_args["model"] == "gpt-4o"
        assert call_args["temperature"] == 0.2
        assert all(cat in call_args["messages"][0]["content"] for cat in service.default_categories)
        
        # Verify result matches one of the default categories
        assert category == "Meeting Notes"
        assert confidence == 0.9
    
    def test_openai_categorization_with_category_matching(self):
        """Test _openai_categorization with response cleanup"""
        # Create service with mocked OpenAI client
        service = CategorizationService()
        service.openai_enabled = True
        
        # Mock OpenAI client with verbose response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "The category is: Work"
        
        service.client = MagicMock()
        service.client.chat.completions.create.return_value = mock_response
        
        # Call _openai_categorization
        category, confidence = service._openai_categorization("Work Update", "Progress on the current project")
        
        # Verify result is cleaned up to match default category
        assert category == "Work"
        assert confidence == 0.9
    
    def test_extract_keywords(self):
        """Test extract_keywords method"""
        # Create service
        service = CategorizationService()
        
        # Test with sample text
        text = "This is a meeting note about the project timeline and budget considerations"
        keywords = service.extract_keywords(text)
        
        # Verify keywords are extracted
        assert len(keywords) <= 5  # Should return at most 5 keywords
        assert "meeting" in keywords
        assert "project" in keywords
        assert "timeline" in keywords
        assert "budget" in keywords
        
        # Verify stop words are removed
        assert "this" not in keywords
        assert "is" not in keywords
        assert "a" not in keywords
        assert "about" not in keywords
        assert "the" not in keywords
        assert "and" not in keywords
    
    def test_extract_keywords_with_empty_text(self):
        """Test extract_keywords with empty text"""
        # Create service
        service = CategorizationService()
        
        # Test with empty text
        keywords = service.extract_keywords("")
        
        # Verify empty list is returned
        assert keywords == []
    
    def test_extract_keywords_with_custom_max(self):
        """Test extract_keywords with custom max_keywords"""
        # Create service
        service = CategorizationService()
        
        # Test with longer text and custom max_keywords
        text = "This is a comprehensive meeting note about the project timeline budget considerations resources allocation team responsibilities and stakeholder engagement"
        keywords = service.extract_keywords(text, max_keywords=3)
        
        # Verify only 3 keywords are returned
        assert len(keywords) == 3