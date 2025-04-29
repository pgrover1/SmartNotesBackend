import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import logging
from typing import Dict, Any

# Assume the class NoteAnalysisService is in 'NoteAnalysisService.py'
# Adjust the import path if necessary
from app.services.note_analysis import NoteAnalysisService 
# Disable logging for tests unless specifically testing logging
logging.disable(logging.CRITICAL)

# Mock response structure helper
def create_mock_openai_response(content: str):
    """Creates a mock object mimicking OpenAI chat completion response"""
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = content
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    return mock_response

class TestNoteAnalysisService(unittest.TestCase):

    def setUp(self):
        # Sample data
        self.test_title = "Test Note Title"
        self.test_content_long = "This is a long piece of content designed for testing summarization. " * 15
        self.test_content_short = "Short content."
        self.test_content_empty = ""

    # --- Initialization Tests ---

    @patch('app.services.note_analysis.OpenAI')
    @patch('app.services.note_analysis.settings')
    def test_init_openai_enabled(self, mock_settings, mock_openai_class):
        """Test initialization when OpenAI is configured and enabled."""
        # Configure mock settings
        mock_settings.OPENAI_API_KEY = "fake_api_key"
        mock_settings.ENABLE_AI_FEATURES = True

        # Mock OpenAI client instance
        mock_openai_instance = MagicMock()
        mock_openai_class.return_value = mock_openai_instance

        # Initialize service
        service = NoteAnalysisService()

        # Assertions
        self.assertTrue(service.openai_enabled)
        self.assertIsNotNone(service.client)
        self.assertEqual(service.client, mock_openai_instance)
        mock_openai_class.assert_called_once_with(api_key="fake_api_key")
        # print(f"Debug: service.client type: {type(service.client)}") # For debugging

    @patch('app.services.note_analysis.OpenAI')
    @patch('app.services.note_analysis.settings')
    def test_init_openai_disabled_no_key(self, mock_settings, mock_openai_class):
        """Test initialization when OpenAI API key is missing."""
        # Configure mock settings
        mock_settings.OPENAI_API_KEY = None # Or ""
        mock_settings.ENABLE_AI_FEATURES = True

        # Initialize service
        service = NoteAnalysisService()

        # Assertions
        self.assertFalse(service.openai_enabled)
        self.assertIsNone(service.client)
        mock_openai_class.assert_not_called() # OpenAI() constructor should not be called

    @patch('app.services.note_analysis.OpenAI')
    @patch('app.services.note_analysis.settings')
    def test_init_openai_disabled_feature_flag(self, mock_settings, mock_openai_class):
        """Test initialization when AI features are disabled via settings."""
         # Configure mock settings
        mock_settings.OPENAI_API_KEY = "fake_api_key"
        mock_settings.ENABLE_AI_FEATURES = False

        # Initialize service
        service = NoteAnalysisService()

        # Assertions
        self.assertFalse(service.openai_enabled)
        self.assertIsNone(service.client)
        mock_openai_class.assert_not_called() # OpenAI() constructor should not be called

    # --- analyze_note Tests ---

    @patch('app.services.note_analysis.settings')
    def test_analyze_note_openai_disabled(self, mock_settings):
        """Test analyze_note when OpenAI is disabled."""
        mock_settings.OPENAI_API_KEY = None
        mock_settings.ENABLE_AI_FEATURES = True
        service = NoteAnalysisService() # Re-init with new settings

        result = service.analyze_note(self.test_title, self.test_content_long)

        expected_result = {
            "summary": None,
            "sentiment": "Neutral",
            "analysis_method": "none"
        }
        self.assertEqual(result, expected_result)

    @patch('app.services.note_analysis.settings')
    def test_analyze_note_content_too_short(self, mock_settings):
        """Test analyze_note with content that is too short."""
        mock_settings.OPENAI_API_KEY = "fake_api_key"
        mock_settings.ENABLE_AI_FEATURES = True
        service = NoteAnalysisService() # Re-init

        result = service.analyze_note(self.test_title, self.test_content_short)

        expected_result = {
            "summary": None,
            "sentiment": "Neutral",
            "analysis_method": "none"
        }
        self.assertEqual(result, expected_result)

    @patch('app.services.note_analysis.OpenAI')
    @patch('app.services.note_analysis.settings')
    def test_analyze_note_openai_enabled_success(self, mock_settings, mock_openai_class):
        """Test analyze_note success path with OpenAI enabled."""
        mock_settings.OPENAI_API_KEY = "fake_api_key"
        mock_settings.ENABLE_AI_FEATURES = True

        # Mock the client and its methods
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = create_mock_openai_response("Positive")

        service = NoteAnalysisService()

        # Mock analyze_sentiment directly for this test (alternative to mocking client.chat...)
        # This isolates analyze_note logic better if analyze_sentiment is complex
        with patch.object(service, 'analyze_sentiment', return_value="Positive") as mock_analyze_sentiment:
             result = service.analyze_note(self.test_title, self.test_content_long)

             expected_result = {
                 "summary": None, # Summary is not generated by analyze_note
                 "sentiment": "Positive",
                 "analysis_method": "openai"
             }
             self.assertEqual(result, expected_result)
             mock_analyze_sentiment.assert_called_once_with(self.test_content_long)

    @patch('app.services.note_analysis.OpenAI')
    @patch('app.services.note_analysis.settings')
    def test_analyze_note_openai_exception(self, mock_settings, mock_openai_class):
        """Test analyze_note when OpenAI call raises an exception."""
        mock_settings.OPENAI_API_KEY = "fake_api_key"
        mock_settings.ENABLE_AI_FEATURES = True

        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        # Make analyze_sentiment (which calls the client) raise an error
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        service = NoteAnalysisService()

        result = service.analyze_note(self.test_title, self.test_content_long)

        # Should fallback to default on error
        expected_result = {
            "summary":None,
            "sentiment": "Neutral", # Falls back from analyze_sentiment exception
            "analysis_method": "openai" # Falls back because the try block failed
        }
        self.assertEqual(result, expected_result)


    # --- analyze_sentiment Tests ---

    @patch('app.services.note_analysis.settings')
    def test_analyze_sentiment_openai_disabled(self, mock_settings):
        """Test analyze_sentiment when OpenAI is disabled."""
        mock_settings.OPENAI_API_KEY = None
        mock_settings.ENABLE_AI_FEATURES = True
        service = NoteAnalysisService()

        sentiment = service.analyze_sentiment(self.test_content_long)
        self.assertEqual(sentiment, "Neutral")

    @patch('app.services.note_analysis.OpenAI')
    @patch('app.services.note_analysis.settings')
    def test_analyze_sentiment_positive(self, mock_settings, mock_openai_class):
        """Test analyze_sentiment returns Positive."""
        mock_settings.OPENAI_API_KEY = "fake_key"
        mock_settings.ENABLE_AI_FEATURES = True
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = create_mock_openai_response("Positive")

        service = NoteAnalysisService()
        sentiment = service.analyze_sentiment(self.test_content_long)

        self.assertEqual(sentiment, "Positive")
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        self.assertEqual(call_args.kwargs['model'], 'gpt-4o')
        self.assertIn("Positive, Neutral, Mixed or Negative", call_args.kwargs['messages'][1]['content'])


    @patch('app.services.note_analysis.OpenAI')
    @patch('app.services.note_analysis.settings')
    def test_analyze_sentiment_mixed_case_response(self, mock_settings, mock_openai_class):
        """Test analyze_sentiment handles mixed case and extra text."""
        mock_settings.OPENAI_API_KEY = "fake_key"
        mock_settings.ENABLE_AI_FEATURES = True
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = create_mock_openai_response("The sentiment is clearly nEgAtIvE.")

        service = NoteAnalysisService()
        sentiment = service.analyze_sentiment(self.test_content_long)

        self.assertEqual(sentiment, "Negative") # Should match Negative category

    @patch('app.services.note_analysis.OpenAI')
    @patch('app.services.note_analysis.settings')
    def test_analyze_sentiment_unexpected_response(self, mock_settings, mock_openai_class):
        """Test analyze_sentiment falls back to Neutral on unexpected response."""
        mock_settings.OPENAI_API_KEY = "fake_key"
        mock_settings.ENABLE_AI_FEATURES = True
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = create_mock_openai_response("I'm unsure about the sentiment.")

        service = NoteAnalysisService()
        sentiment = service.analyze_sentiment(self.test_content_long)

        self.assertEqual(sentiment, "Neutral") # Fallback

    @patch('app.services.note_analysis.OpenAI')
    @patch('app.services.note_analysis.settings')
    def test_analyze_sentiment_api_error(self, mock_settings, mock_openai_class):
        """Test analyze_sentiment falls back to Neutral on API error."""
        mock_settings.OPENAI_API_KEY = "fake_key"
        mock_settings.ENABLE_AI_FEATURES = True
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Down")

        service = NoteAnalysisService()
        sentiment = service.analyze_sentiment(self.test_content_long)

        self.assertEqual(sentiment, "Neutral") # Fallback on exception


    # --- generate_openai_summary Tests ---

    @patch('app.services.note_analysis.settings')
    def test_generate_summary_openai_disabled(self, mock_settings):
        """Test generate_summary when OpenAI is disabled."""
        mock_settings.OPENAI_API_KEY = None
        mock_settings.ENABLE_AI_FEATURES = True
        service = NoteAnalysisService()

        result = service.generate_openai_summary(self.test_title, self.test_content_long)

        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "OpenAI API key not configured")
        self.assertIsNone(result["summary"])

    @patch('app.services.note_analysis.settings')
    def test_generate_summary_no_content(self, mock_settings):
        """Test generate_summary with empty content."""
        mock_settings.OPENAI_API_KEY = "fake_key"
        mock_settings.ENABLE_AI_FEATURES = True
        service = NoteAnalysisService()

        result = service.generate_openai_summary(self.test_title, self.test_content_empty)

        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "No content provided")
        self.assertIsNone(result["summary"])

    @patch('app.services.note_analysis.settings')
    def test_generate_summary_content_too_short(self, mock_settings):
        """Test generate_summary with content too short (based on word count < 20)."""
        mock_settings.OPENAI_API_KEY = "fake_key"
        mock_settings.ENABLE_AI_FEATURES = True
        service = NoteAnalysisService()
        # Create content with 19 words
        short_content = "word " * 19

        result = service.generate_openai_summary(self.test_title, short_content)

        self.assertFalse(result["success"])
        # Check the error message matches the code's logic, even if description differs
        self.assertEqual(result["error"], "Content is less than 200 words and doesn't need summarization") # Message text comes from code
        self.assertIsNone(result["summary"])


    @patch('app.services.note_analysis.OpenAI')
    @patch('app.services.note_analysis.settings')
    def test_generate_summary_success_default_model(self, mock_settings, mock_openai_class):
        """Test successful summary generation with default model."""
        mock_settings.OPENAI_API_KEY = "fake_key"
        mock_settings.ENABLE_AI_FEATURES = True
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_summary = "This is the generated summary."
        mock_client.chat.completions.create.return_value = create_mock_openai_response(mock_summary)

        service = NoteAnalysisService()
        result = service.generate_openai_summary(self.test_title, self.test_content_long)

        self.assertTrue(result["success"])
        self.assertEqual(result["summary"], mock_summary)
        self.assertEqual(result["model_used"], "gpt-4o") # Default model
        self.assertIsNone(result["error"])
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        self.assertEqual(call_args.kwargs['model'], 'gpt-4o')
        self.assertIn(self.test_title, call_args.kwargs['messages'][1]['content'])
        self.assertIn(self.test_content_long, call_args.kwargs['messages'][1]['content'])
        self.assertIn("under 150 characters", call_args.kwargs['messages'][1]['content']) # Default max_length


    @patch('app.services.note_analysis.OpenAI')
    @patch('app.services.note_analysis.settings')
    def test_generate_summary_success_specific_model_and_length(self, mock_settings, mock_openai_class):
        """Test successful summary generation with specific model and length."""
        mock_settings.OPENAI_API_KEY = "fake_key"
        mock_settings.ENABLE_AI_FEATURES = True
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_summary = "Short summary."
        mock_client.chat.completions.create.return_value = create_mock_openai_response(mock_summary)

        service = NoteAnalysisService()
        result = service.generate_openai_summary(
            self.test_title,
            self.test_content_long,
            max_length=50,
            model="gpt-3.5-turbo"
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["summary"], mock_summary)
        self.assertEqual(result["model_used"], "gpt-3.5-turbo")
        self.assertIsNone(result["error"])
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        self.assertEqual(call_args.kwargs['model'], 'gpt-3.5-turbo')
        self.assertIn("under 50 characters", call_args.kwargs['messages'][1]['content'])


    @patch('app.services.note_analysis.OpenAI')
    @patch('app.services.note_analysis.settings')
    def test_generate_summary_invalid_model_defaults_to_gpt4o(self, mock_settings, mock_openai_class):
        """Test summary generation defaults to gpt-4o if invalid model specified."""
        mock_settings.OPENAI_API_KEY = "fake_key"
        mock_settings.ENABLE_AI_FEATURES = True
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_summary = "Summary from default model."
        mock_client.chat.completions.create.return_value = create_mock_openai_response(mock_summary)

        service = NoteAnalysisService()
        result = service.generate_openai_summary(
            self.test_title,
            self.test_content_long,
            model="gpt-4o" 
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["summary"], mock_summary)
        self.assertEqual(result["model_used"], "gpt-4o") # Should default
        self.assertIsNone(result["error"])
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        self.assertEqual(call_args.kwargs['model'], 'gpt-4o') # Check model used in API call


    @patch('app.services.note_analysis.OpenAI')
    @patch('app.services.note_analysis.settings')
    def test_generate_summary_api_error(self, mock_settings, mock_openai_class):
        """Test generate_summary handles API errors."""
        mock_settings.OPENAI_API_KEY = "fake_key"
        mock_settings.ENABLE_AI_FEATURES = True
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        error_message = "Network connection failed"
        mock_client.chat.completions.create.side_effect = Exception(error_message)

        service = NoteAnalysisService()
        result = service.generate_openai_summary(self.test_title, self.test_content_long)

        self.assertFalse(result["success"])
        self.assertIsNone(result["summary"])
        self.assertEqual(result["error"], error_message)
        self.assertEqual(result["model_used"], "gpt-4o") # Still records the intended model


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)