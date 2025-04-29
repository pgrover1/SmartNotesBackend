import pytest
from unittest.mock import MagicMock, patch
import logging
from bson import ObjectId  # Import ObjectId if category IDs are MongoDB ObjectIds

# Assume the class CategorizationService is in 'app.services.categorization.py'
# Adjust the import path if necessary.
try:
    from app.services.categorization import CategorizationService
except ImportError:
    # If the actual class isn't found, create a placeholder mock structure
    # This allows writing tests, but they won't run without the real class.
    class MockSettings:
        OPENAI_API_KEY = None
        ENABLE_AI_FEATURES = False

    class MockCategoryRepository:
        def get_categories(self):
            return [] # Default mock implementation

    # Mock the repository at the source location if needed globally
    # patch('app.repositories.category_mongodb.category_repository', MockCategoryRepository(), create=True)

    class CategorizationService:
        def __init__(self):
            # Mock initialization based on how tests use it
            with patch('app.services.categorization.settings', MockSettings, create=True):
                 self.api_key = MockSettings.OPENAI_API_KEY
                 self.openai_enabled = bool(self.api_key) and MockSettings.ENABLE_AI_FEATURES
                 self.client = None
                 if self.openai_enabled:
                     with patch('app.services.categorization.OpenAI') as mock_openai:
                         self.client = mock_openai(api_key=self.api_key)

            # Mock methods used in tests if the real class isn't available
            if not hasattr(self, '_openai_categorization'):
                 self._openai_categorization = MagicMock(return_value=("Uncategorized", None, 0.0))
            if not hasattr(self, 'extract_keywords'):
                 self.extract_keywords = MagicMock(return_value=[])
            if not hasattr(self, 'suggest_category'):
                 self.suggest_category = MagicMock(return_value={
                    "category": "Uncategorized",
                    "category_id": None,
                    "confidence": 0.0,
                    "keywords": [],
                    "method": "default"
                 })

# Disable logging for tests unless specifically testing logging
logging.disable(logging.CRITICAL)

# Mock response structure helper for OpenAI calls
def create_mock_openai_response(content: str):
    """Creates a mock object mimicking OpenAI chat completion response"""
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = content
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    return mock_response

# Sample categories data mimicking repository response
SAMPLE_CATEGORY_ID_WORK = str(ObjectId()) # Generate a realistic ObjectId string
SAMPLE_CATEGORY_ID_PERSONAL = str(ObjectId())
SAMPLE_CATEGORIES_DB = [
    {"id": SAMPLE_CATEGORY_ID_WORK, "name": "Work"},
    {"id": SAMPLE_CATEGORY_ID_PERSONAL, "name": "Personal Project"},
]
EMPTY_CATEGORIES_DB = []


# --- Test Class ---
class TestCategorizationService:
    """Tests for the CategorizationService"""

    # --- Fixtures ---

    @pytest.fixture
    def mock_settings(self):
        """Fixture to mock settings."""
        with patch('app.services.categorization.settings', create=True) as mock_settings_obj:
            # Default values
            mock_settings_obj.OPENAI_API_KEY = None
            mock_settings_obj.ENABLE_AI_FEATURES = False
            yield mock_settings_obj

    @pytest.fixture
    def mock_openai_client(self):
        """Fixture to mock the OpenAI client class."""
        with patch('app.services.categorization.OpenAI', create=True) as mock_openai_class:
            mock_instance = MagicMock()
            # Mock the specific method used
            mock_instance.chat.completions.create = MagicMock()
            mock_openai_class.return_value = mock_instance
            yield mock_openai_class, mock_instance # Yield class and instance

    @pytest.fixture
    def mock_category_repo(self):
        """Fixture to mock the category repository."""
        with patch('app.services.categorization.category_repository', create=True) as mock_repo:
            # Default behavior: return sample categories
            mock_repo.get_categories.return_value = SAMPLE_CATEGORIES_DB
            yield mock_repo

    @pytest.fixture
    def service_instance(self, mock_settings, mock_openai_client, mock_category_repo):
        """Fixture to create a service instance with mocked dependencies."""
        # Note: The mocks are active due to the context managers in their fixtures
        # We just need to ensure settings are configured correctly *before* init
        mock_settings.OPENAI_API_KEY = "test-api-key"
        mock_settings.ENABLE_AI_FEATURES = True
        service = CategorizationService()
        # Manually attach mocks if needed for direct access in tests, though often not required
        service.mock_settings = mock_settings
        service.mock_openai_class, service.mock_openai_instance = mock_openai_client
        service.mock_category_repo = mock_category_repo
        return service

    @pytest.fixture
    def service_instance_openai_disabled(self, mock_settings, mock_openai_client, mock_category_repo):
        """Fixture for service instance with OpenAI explicitly disabled."""
        mock_settings.OPENAI_API_KEY = None # Disable via key
        mock_settings.ENABLE_AI_FEATURES = True
        service = CategorizationService()
         # Manually attach mocks if needed
        service.mock_settings = mock_settings
        service.mock_openai_class, service.mock_openai_instance = mock_openai_client
        service.mock_category_repo = mock_category_repo
        return service

    # --- Initialization Tests ---

    def test_init_with_openai_enabled(self, mock_settings, mock_openai_client, mock_category_repo):
        """Test initialization when OpenAI is enabled"""
        mock_settings.OPENAI_API_KEY = "test-api-key"
        mock_settings.ENABLE_AI_FEATURES = True
        mock_openai_class, mock_openai_instance = mock_openai_client

        service = CategorizationService()

        assert service.openai_enabled is True
        assert service.client == mock_openai_instance
        mock_openai_class.assert_called_once_with(api_key="test-api-key")
        mock_category_repo.get_categories.assert_not_called() # Repo not called during init

    def test_init_with_openai_disabled_no_key(self, mock_settings, mock_openai_client, mock_category_repo):
        """Test initialization when OpenAI API key is missing"""
        mock_settings.OPENAI_API_KEY = "" # Or None
        mock_settings.ENABLE_AI_FEATURES = True
        mock_openai_class, _ = mock_openai_client

        service = CategorizationService()

        assert service.openai_enabled is False
        assert service.client is None
        mock_openai_class.assert_not_called()

    def test_init_with_openai_disabled_feature_flag(self, mock_settings, mock_openai_client, mock_category_repo):
        """Test initialization when AI features are disabled via settings"""
        mock_settings.OPENAI_API_KEY = "test-api-key"
        mock_settings.ENABLE_AI_FEATURES = False # Feature flag off
        mock_openai_class, _ = mock_openai_client

        service = CategorizationService()

        assert service.openai_enabled is False
        assert service.client is None
        mock_openai_class.assert_not_called()


    # --- suggest_category Tests ---

    def test_suggest_category_with_empty_input(self, service_instance_openai_disabled):
        """Test suggest_category with empty title and content"""
        service = service_instance_openai_disabled # Doesn't matter if OpenAI enabled or not

        # Mock extract_keywords as it shouldn't be called if input is empty
        with patch.object(service, 'extract_keywords') as mock_extract:
            result = service.suggest_category("", "")

            # Verify default response
            assert result == {
                "category": "Uncategorized",
                "category_id": None,
                "confidence": 0.0,
                "keywords": [],
                "method": "default"
            }
            mock_extract.assert_not_called() # Keyword extraction skipped

    def test_suggest_category_with_openai_disabled(self, service_instance_openai_disabled):
        """Test suggest_category when OpenAI is disabled"""
        service = service_instance_openai_disabled

        # Mock extract_keywords as it's called in the default path
        with patch.object(service, 'extract_keywords', return_value=["meeting", "project"]) as mock_extract:
            # Mock _openai_categorization to ensure it's not called
            with patch.object(service, '_openai_categorization') as mock_openai_cat:
                result = service.suggest_category("Work Meeting", "Notes from today's project meeting")

                # Verify default response with extracted keywords
                assert result == {
                    "category": "Uncategorized",
                    "category_id": None,
                    "confidence": 0.0,
                    "keywords": ["meeting", "project"],
                    "method": "default"
                }
                # Check extract_keywords was called correctly (title duplicated)
                mock_extract.assert_called_once_with("Work Meeting Work Meeting Notes from today's project meeting")
                mock_openai_cat.assert_not_called() # OpenAI method skipped

    def test_suggest_category_with_openai_enabled_success(self, service_instance):
        """Test suggest_category when OpenAI is enabled and succeeds"""
        service = service_instance
        expected_keywords = ["meeting", "project"]
        expected_category = "Work"
        expected_category_id = SAMPLE_CATEGORY_ID_WORK
        expected_confidence = 0.9

        # Mock the internal OpenAI call and keyword extraction
        with patch.object(service, '_openai_categorization', return_value=(expected_category, expected_category_id, expected_confidence)) as mock_openai_cat, \
             patch.object(service, 'extract_keywords', return_value=expected_keywords) as mock_extract:

            result = service.suggest_category("Work Meeting", "Notes from today's project meeting")

            # Verify OpenAI response is used
            assert result == {
                "category": expected_category,
                "category_id": expected_category_id,
                "confidence": expected_confidence,
                "keywords": expected_keywords,
                "method": "openai"
            }
            mock_openai_cat.assert_called_once_with("Work Meeting", "Notes from today's project meeting")
            mock_extract.assert_called_once_with("Work Meeting Work Meeting Notes from today's project meeting")

    def test_suggest_category_with_openai_error(self, service_instance):
        """Test suggest_category when OpenAI throws an error"""
        service = service_instance
        expected_keywords = ["meeting", "project"]

        # Mock _openai_categorization to raise exception and mock keyword extraction
        with patch.object(service, '_openai_categorization', side_effect=Exception("API error")) as mock_openai_cat, \
             patch.object(service, 'extract_keywords', return_value=expected_keywords) as mock_extract:

            result = service.suggest_category("Work Meeting", "Notes from today's project meeting")

            # Verify fallback to default response
            assert result == {
                "category": "Uncategorized",
                "category_id": None,
                "confidence": 0.0,
                "keywords": expected_keywords, # Keywords should still be extracted
                "method": "default" # Falls back to default
            }
            mock_openai_cat.assert_called_once_with("Work Meeting", "Notes from today's project meeting")
            mock_extract.assert_called_once_with("Work Meeting Work Meeting Notes from today's project meeting")


    # --- _openai_categorization Tests ---

    def test_openai_categorization_success_match(self, service_instance):
        """Test _openai_categorization successfully returns a matched category and ID"""
        service = service_instance
        mock_openai_instance = service.mock_openai_instance
        mock_category_repo = service.mock_category_repo

        # Configure mocks
        mock_category_repo.get_categories.return_value = SAMPLE_CATEGORIES_DB
        mock_openai_instance.chat.completions.create.return_value = create_mock_openai_response("Work")

        # Call the private method
        category, category_id, confidence = service._openai_categorization("Team Sync", "Discuss project updates")

        # Verify repo call
        mock_category_repo.get_categories.assert_called_once()

        # Verify OpenAI call
        mock_openai_instance.chat.completions.create.assert_called_once()
        call_args = mock_openai_instance.chat.completions.create.call_args.kwargs
        assert call_args["model"] == "gpt-4o"
        assert call_args["temperature"] == 0.2
        assert "Categorize the following note" in call_args["messages"][1]["content"]
        # Check categories from DB are in the prompt
        assert "Work" in call_args["messages"][1]["content"]
        assert "Personal Project" in call_args["messages"][1]["content"]
        assert "Team Sync" in call_args["messages"][1]["content"]
        assert "Discuss project updates" in call_args["messages"][1]["content"]

        # Verify result
        assert category == "Work"
        assert category_id == SAMPLE_CATEGORY_ID_WORK
        assert confidence == 0.9 # Fixed confidence in current implementation

    def test_openai_categorization_success_partial_match_cleanup(self, service_instance):
        """Test _openai_categorization cleans up response and finds category ID"""
        service = service_instance
        mock_openai_instance = service.mock_openai_instance
        mock_category_repo = service.mock_category_repo

        # Configure mocks
        mock_category_repo.get_categories.return_value = SAMPLE_CATEGORIES_DB
        # Simulate OpenAI response needing cleanup
        mock_openai_instance.chat.completions.create.return_value = create_mock_openai_response("This looks like a Personal Project.")

        category, category_id, confidence = service._openai_categorization("My Side Hustle", "Ideas for the app")

        assert category == "Personal Project" # Cleaned category name
        assert category_id == SAMPLE_CATEGORY_ID_PERSONAL
        assert confidence == 0.9
        mock_category_repo.get_categories.assert_called_once()
        mock_openai_instance.chat.completions.create.assert_called_once()

    def test_openai_categorization_no_db_categories(self, service_instance):
        """Test _openai_categorization returns Uncategorized if DB has no categories"""
        service = service_instance
        mock_openai_instance = service.mock_openai_instance
        mock_category_repo = service.mock_category_repo

        # Configure mocks
        mock_category_repo.get_categories.return_value = EMPTY_CATEGORIES_DB # No categories

        category, category_id, confidence = service._openai_categorization("Test Title", "Test Content")

        # Verify result is default, OpenAI not called
        assert category == "Uncategorized"
        assert category_id is None
        assert confidence == 0.0
        mock_category_repo.get_categories.assert_called_once()
        mock_openai_instance.chat.completions.create.assert_not_called() # Skips OpenAI call

    def test_openai_categorization_openai_response_no_match(self, service_instance):
        """Test _openai_categorization when OpenAI response doesn't match any known category"""
        service = service_instance
        mock_openai_instance = service.mock_openai_instance
        mock_category_repo = service.mock_category_repo

        # Configure mocks
        mock_category_repo.get_categories.return_value = SAMPLE_CATEGORIES_DB
        # Simulate OpenAI response that doesn't contain known category keywords
        openai_raw_response = "This note is about general tasks."
        mock_openai_instance.chat.completions.create.return_value = create_mock_openai_response(openai_raw_response)

        category, category_id, confidence = service._openai_categorization("Random Tasks", "List of things to do")

        # Current implementation returns the raw response if no keyword match found
        assert category == openai_raw_response
        assert category_id is None # No ID found
        assert confidence == 0.9 # Still returns fixed confidence

        mock_category_repo.get_categories.assert_called_once()
        mock_openai_instance.chat.completions.create.assert_called_once()
        # Note: A potentially better behavior here might be to return "Uncategorized", None, 0.5

    def test_openai_categorization_openai_api_error(self, service_instance):
        """Test _openai_categorization handles OpenAI API errors"""
        service = service_instance
        mock_openai_instance = service.mock_openai_instance
        mock_category_repo = service.mock_category_repo

        # Configure mocks
        mock_category_repo.get_categories.return_value = SAMPLE_CATEGORIES_DB
        error_message = "API connection failed"
        mock_openai_instance.chat.completions.create.side_effect = Exception(error_message)

        # Expect the exception to be raised upwards
        with pytest.raises(Exception, match=error_message):
            service._openai_categorization("Error Test", "This should fail")

        mock_category_repo.get_categories.assert_called_once()
        mock_openai_instance.chat.completions.create.assert_called_once()

    def test_openai_categorization_repo_error(self, service_instance):
        """Test _openai_categorization handles category repository errors"""
        service = service_instance
        mock_openai_instance = service.mock_openai_instance
        mock_category_repo = service.mock_category_repo

        # Configure mocks
        error_message = "Database connection failed"
        mock_category_repo.get_categories.side_effect = Exception(error_message)

        # Expect the exception to be raised upwards
        with pytest.raises(Exception, match=error_message):
            service._openai_categorization("Error Test", "This should fail")

        mock_category_repo.get_categories.assert_called_once()
        mock_openai_instance.chat.completions.create.assert_not_called() # OpenAI call skipped


    # --- extract_keywords Tests ---
    # These tests don't need the full service instance fixture with external mocks

    @pytest.fixture
    def keyword_service(self):
        """Basic service instance just for keyword extraction"""
        # No need to mock external dependencies for these tests
        with patch('app.services.categorization.settings'), \
             patch('app.services.categorization.OpenAI'), \
             patch('app.services.categorization.category_repository'):
            service = CategorizationService()
        return service

    def test_extract_keywords_standard(self, keyword_service):
        """Test extract_keywords method with standard text"""
        text = "This is a meeting note about the project timeline and budget considerations."
        keywords = keyword_service.extract_keywords(text)
        assert len(keywords) <= 5
        assert "meeting" in keywords
        assert "note" in keywords # 'note' is not in default stop words
        assert "project" in keywords
        assert "timeline" in keywords
        assert "budget" in keywords
        # Verify stop words are removed
        assert "this" not in keywords
        assert "is" not in keywords
        assert "a" not in keywords
        assert "the" not in keywords
        assert "and" not in keywords

    def test_extract_keywords_with_empty_text(self, keyword_service):
        """Test extract_keywords with empty text"""
        keywords = keyword_service.extract_keywords("")
        assert keywords == []

    def test_extract_keywords_with_custom_max(self, keyword_service):
        """Test extract_keywords with custom max_keywords"""
        text = "Comprehensive meeting note: project timeline, budget, resources, allocation, team, responsibilities, stakeholders."
        keywords = keyword_service.extract_keywords(text, max_keywords=3)
        assert len(keywords) == 3
        # Check if the most frequent non-stopwords are picked
        assert "meeting" in keywords or "note" in keywords or "project" in keywords # Example check

    def test_extract_keywords_with_punctuation_and_case(self, keyword_service):
        """Test extract_keywords handles punctuation and mixed case"""
        text = "Meeting! Discuss PROJECT Budget? Timeline... OK."
        keywords = keyword_service.extract_keywords(text)
        assert "meeting" in keywords
        assert "discuss" in keywords # 'discuss' not a stop word
        assert "project" in keywords
        assert "budget" in keywords
        assert "timeline" in keywords
        # Check lowercase conversion and punctuation removal
        assert "ok" not in keywords # 'ok' might be too short (len > 2 filter)
        assert "meeting!" not in keywords
        assert "budget?" not in keywords

    def test_extract_keywords_only_stopwords_or_short(self, keyword_service):
        """Test extract_keywords with text containing only stopwords or short words"""
        text = "is the a and for of it go ok"
        keywords = keyword_service.extract_keywords(text)
        assert keywords == [] # 'go', 'ok' filtered by len > 2

