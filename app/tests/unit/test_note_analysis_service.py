import pytest
from unittest.mock import MagicMock, patch
from app.services.note_analysis import NoteAnalysisService

class TestNoteAnalysisService:
    """Tests for the NoteAnalysisService"""

    def test_init_with_openai_enabled(self):
        """Test initialization when OpenAI is enabled"""
        with patch('app.services.note_analysis_service.settings') as mock_settings, \
             patch('app.services.note_analysis_service.OpenAI') as mock_openai:
            
            # Configure mock settings
            mock_settings.OPENAI_API_KEY = "test-api-key"
            mock_settings.ENABLE_AI_FEATURES = True
            
            # Create service
            service = NoteAnalysisService()
            
            # Verify client was initialized
            assert service.openai_enabled is True
            mock_openai.assert_called_once_with(api_key="test-api-key")

    def test_init_with_openai_disabled(self):
        """Test initialization when OpenAI is disabled"""
        with patch('app.services.note_analysis_service.settings') as mock_settings, \
             patch('app.services.note_analysis_service.OpenAI') as mock_openai:
            
            # Configure mock settings with no API key
            mock_settings.OPENAI_API_KEY = ""
            mock_settings.ENABLE_AI_FEATURES = True
            
            # Create service
            service = NoteAnalysisService()
            
            # Verify client was not initialized
            assert service.openai_enabled is False
            mock_openai.assert_not_called()

    def test_analyze_note_with_openai_disabled(self):
        """Test analyze_note when OpenAI is disabled"""
        # Create service with OpenAI disabled
        service = NoteAnalysisService()
        service.openai_enabled = False
        
        # Call analyze_note
        result = service.analyze_note("Test Title", "This is a test note with enough content to be analyzed")
        
        # Verify default response
        assert result["summary"] is None
        assert result["sentiment"] == "Neutral"
        assert result["analysis_method"] == "none"

    def test_analyze_note_with_short_content(self):
        """Test analyze_note with content that's too short"""
        # Create service
        service = NoteAnalysisService()
        service.openai_enabled = True
        
        # Call analyze_note with short content
        result = service.analyze_note("Test Title", "Short")
        
        # Verify default response
        assert result["summary"] is None
        assert result["sentiment"] == "Neutral"
        assert result["analysis_method"] == "none"

    def test_analyze_note_with_openai_enabled(self):
        """Test analyze_note when OpenAI is enabled"""
        # Create service with mocked OpenAI client
        service = NoteAnalysisService()
        service.openai_enabled = True
        service.client = MagicMock()
        
        # Mock generate_summary and analyze_sentiment
        with patch.object(service, 'generate_summary', return_value="Test summary"), \
             patch.object(service, 'analyze_sentiment', return_value="Positive"):
            
            # Call analyze_note
            result = service.analyze_note("Test Title", "This is a test note with enough content to be analyzed")
            
            # Verify OpenAI response
            assert result["summary"] == "Test summary"
            assert result["sentiment"] == "Positive"
            assert result["analysis_method"] == "openai"

    def test_generate_summary_with_openai_disabled(self):
        """Test generate_summary when OpenAI is disabled"""
        # Create service with OpenAI disabled
        service = NoteAnalysisService()
        service.openai_enabled = False
        
        # Call generate_summary
        result = service.generate_summary("Test Title", "This is a test note with enough content to be summarized")
        
        # Verify result is None
        assert result is None

    def test_generate_summary_with_short_content(self):
        """Test generate_summary with content that's too short"""
        # Create service
        service = NoteAnalysisService()
        service.openai_enabled = True
        
        # Call generate_summary with short content
        result = service.generate_summary("Test Title", "Short")
        
        # Verify result is None
        assert result is None

    def test_generate_summary_with_openai_enabled(self):
        """Test generate_summary when OpenAI is enabled"""
        # Create service with mocked OpenAI client
        service = NoteAnalysisService()
        service.openai_enabled = True
        
        # Mock OpenAI client response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is a test summary."
        
        service.client = MagicMock()
        service.client.chat.completions.create.return_value = mock_response
        
        # Call generate_summary
        result = service.generate_summary("Test Title", "This is a test note with enough content to be summarized")
        
        # Verify OpenAI was called with correct parameters
        service.client.chat.completions.create.assert_called_once()
        call_args = service.client.chat.completions.create.call_args[1]
        assert call_args["model"] == "gpt-4o"
        assert call_args["temperature"] == 0.3
        assert "Summarize" in call_args["messages"][1]["content"]
        
        # Verify result
        assert result == "This is a test summary."

    def test_analyze_sentiment_with_openai_disabled(self):
        """Test analyze_sentiment when OpenAI is disabled"""
        # Create service with OpenAI disabled
        service = NoteAnalysisService()
        service.openai_enabled = False
        
        # Call analyze_sentiment
        result = service.analyze_sentiment("This is a positive test note")
        
        # Verify default sentiment
        assert result == "Neutral"

    def test_analyze_sentiment_with_openai_enabled(self):
        """Test analyze_sentiment when OpenAI is enabled"""
        # Create service with mocked OpenAI client
        service = NoteAnalysisService()
        service.openai_enabled = True
        
        # Mock OpenAI client response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Positive"
        
        service.client = MagicMock()
        service.client.chat.completions.create.return_value = mock_response
        
        # Call analyze_sentiment
        result = service.analyze_sentiment("This is a positive test note")
        
        # Verify OpenAI was called with correct parameters
        service.client.chat.completions.create.assert_called_once()
        call_args = service.client.chat.completions.create.call_args[1]
        assert call_args["model"] == "gpt-4o"
        assert call_args["temperature"] == 0.1
        assert "sentiment" in call_args["messages"][1]["content"].lower()
        
        # Verify result
        assert result == "Positive"

    def test_analyze_sentiment_with_unexpected_response(self):
        """Test analyze_sentiment with unexpected response from OpenAI"""
        # Create service with mocked OpenAI client
        service = NoteAnalysisService()
        service.openai_enabled = True
        
        # Mock OpenAI client response with unexpected value
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Happy"  # Not in the expected categories
        
        service.client = MagicMock()
        service.client.chat.completions.create.return_value = mock_response
        
        # Call analyze_sentiment
        result = service.analyze_sentiment("This is a positive test note")
        
        # Verify default sentiment when response doesn't match categories
        assert result == "Neutral"

    def test_generate_openai_summary_with_openai_disabled(self):
        """Test generate_openai_summary when OpenAI is disabled"""
        # Create service with OpenAI disabled
        service = NoteAnalysisService()
        service.openai_enabled = False
        
        # Call generate_openai_summary
        result = service.generate_openai_summary("Test Title", "This is a test note")
        
        # Verify error response
        assert result["summary"] is None
        assert result["success"] is False
        assert "OpenAI API key not configured" in result["error"]

    def test_generate_openai_summary_with_empty_content(self):
        """Test generate_openai_summary with empty content"""
        # Create service
        service = NoteAnalysisService()
        service.openai_enabled = True
        
        # Call generate_openai_summary with empty content
        result = service.generate_openai_summary("Test Title", "")
        
        # Verify error response
        assert result["summary"] is None
        assert result["success"] is False
        assert "No content provided" in result["error"]

    def test_generate_openai_summary_with_invalid_model(self):
        """Test generate_openai_summary with invalid model"""
        # Create service with mocked OpenAI client
        service = NoteAnalysisService()
        service.openai_enabled = True
        
        # Mock OpenAI client response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is a test summary."
        
        service.client = MagicMock()
        service.client.chat.completions.create.return_value = mock_response
        
        # Call generate_openai_summary with invalid model
        result = service.generate_openai_summary("Test Title", "This is a test note", model="invalid-model")
        
        # Verify OpenAI was called with default model
        service.client.chat.completions.create.assert_called_once()
        call_args = service.client.chat.completions.create.call_args[1]
        assert call_args["model"] == "gpt-4o"  # Should default to gpt-4o
        
        # Verify successful response
        assert result["summary"] == "This is a test summary."
        assert result["success"] is True
        assert result["model_used"] == "gpt-4o"

    def test_generate_openai_summary_with_custom_length(self):
        """Test generate_openai_summary with custom max_length"""
        # Create service with mocked OpenAI client
        service = NoteAnalysisService()
        service.openai_enabled = True
        
        # Mock OpenAI client response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is a short summary."
        
        service.client = MagicMock()
        service.client.chat.completions.create.return_value = mock_response
        
        # Call generate_openai_summary with custom max_length
        result = service.generate_openai_summary("Test Title", "This is a test note", max_length=50)
        
        # Verify OpenAI was called with correct parameters
        service.client.chat.completions.create.assert_called_once()
        call_args = service.client.chat.completions.create.call_args[1]
        assert "50 characters" in call_args["messages"][1]["content"]
        # Verify max_tokens is calculated based on max_length
        assert call_args["max_tokens"] == 100  # should be min 100
        
        # Verify successful response
        assert result["summary"] == "This is a short summary."
        assert result["success"] is True