import pytest
from unittest.mock import MagicMock, patch
from bson import ObjectId # If using MongoDB ObjectIds

# Assuming schemas are Pydantic models or similar structures
class MockCategoryCreate:
    def __init__(self, name: str, description: str = None):
        self.name = name
        self.description = description

class MockCategoryUpdate:
    def __init__(self, name: str = None, description: str = None):
        # Pydantic models often exclude unset fields, mimic this if needed
        self.name = name
        self.description = description
        # Simulate Pydantic's model_dump(exclude_unset=True) if repo needs it
        self.model_dump_dict = {k: v for k, v in vars(self).items() if v is not None}

    def model_dump(self, exclude_unset=True):
         if exclude_unset:
             return self.model_dump_dict
         return vars(self)


# Assume the class CategoryMongoService is in 'app.services.categories.py'
# Adjust the import path if necessary.
try:
    from app.services.categories import CategoryMongoService
except ImportError:
    # Placeholder if the actual class isn't found during test writing
    class CategoryMongoService:
        # Basic mock structure if needed for type hinting/autocompletion
        def get_category(self, db, category_id: str): pass
        def get_categories(self, db, skip: int = 0, limit: int = 100): pass
        def create_category(self, db, category_in): pass
        def update_category(self, db, category_id: str, category_in): pass
        def delete_category(self, db, category_id: str): pass
        def suggest_category(self, db, content: str): pass


# --- Test Data ---
TEST_CATEGORY_ID_1 = str(ObjectId())
TEST_CATEGORY_ID_2 = str(ObjectId())
TEST_CATEGORY_1 = {"id": TEST_CATEGORY_ID_1, "name": "Work", "description": "Work related notes"}
TEST_CATEGORY_2 = {"id": TEST_CATEGORY_ID_2, "name": "Personal", "description": "Personal stuff"}
ALL_CATEGORIES = [TEST_CATEGORY_1, TEST_CATEGORY_2]


# --- Fixtures for Mocks ---

@pytest.fixture
def mock_category_repository():
    """Fixture to mock the category repository dependency."""
    # Patch where the repository is looked up (imported) in the service module
    with patch('app.services.categories.category_repository', create=True) as mock_repo:
        yield mock_repo

@pytest.fixture
def mock_categorization_service():
    """Fixture to mock the categorization service dependency."""
    # Patch where the service is looked up (imported) in the service module
    with patch('app.services.categories.categorization_service', create=True) as mock_service:
        yield mock_service


# --- Test Class ---
class TestCategoryMongoService:
    """Tests for the CategoryMongoService"""

    @pytest.fixture(autouse=True)
    def setup_mocks(self, mock_categorization_service, mock_category_repository):
        """
        Injects mocks into the test class instance for easier access
        and resets them before each test. This fixture now correctly
        receives the mocks defined above.
        """
        self.mock_categorization_service = mock_categorization_service
        self.mock_category_repository = mock_category_repository
        # Reset mocks before each test run
        self.mock_categorization_service.reset_mock()
        self.mock_category_repository.reset_mock()

    @pytest.fixture
    def service_instance(self, mock_category_repository, mock_categorization_service):
        """
        Fixture to create a new service instance for each test.
        Crucially, it depends on the mock fixtures to ensure the patches
        are active *before* the service is instantiated.
        """
        # The patches from the mock fixtures are active here
        service = CategoryMongoService()
        # Optionally attach mocks to service instance if needed within methods,
        # but usually accessing via self.mock_* is sufficient in tests.
        # service.category_repository = mock_category_repository # Example if needed
        # service.categorization_service = mock_categorization_service # Example if needed
        return service

    # --- get_category Tests ---

    def test_get_category_found(self, service_instance):
        """Test get_category when category exists"""
        # Access mocks via self, set up by setup_mocks fixture
        self.mock_category_repository.get_category.return_value = TEST_CATEGORY_1

        result = service_instance.get_category(None, TEST_CATEGORY_ID_1) # db is unused

        assert result == TEST_CATEGORY_1
        self.mock_category_repository.get_category.assert_called_once_with(TEST_CATEGORY_ID_1)

    def test_get_category_not_found(self, service_instance):
        """Test get_category when category does not exist"""
        self.mock_category_repository.get_category.return_value = None
        category_id = str(ObjectId())

        result = service_instance.get_category(None, category_id)

        assert result is None
        self.mock_category_repository.get_category.assert_called_once_with(category_id)

    # --- get_categories Tests ---

    def test_get_categories_success(self, service_instance):
        """Test get_categories successfully retrieves categories"""
        self.mock_category_repository.get_categories.return_value = ALL_CATEGORIES

        result = service_instance.get_categories(None, skip=5, limit=50) # db is unused

        assert result == ALL_CATEGORIES
        self.mock_category_repository.get_categories.assert_called_once_with(skip=5, limit=50)

    def test_get_categories_default_pagination(self, service_instance):
        """Test get_categories with default pagination"""
        self.mock_category_repository.get_categories.return_value = ALL_CATEGORIES

        result = service_instance.get_categories(None) # db is unused

        assert result == ALL_CATEGORIES
        self.mock_category_repository.get_categories.assert_called_once_with(skip=0, limit=100)

    # --- create_category Tests ---

    def test_create_category_success(self, service_instance):
        """Test create_category when name does not exist"""
        category_data = MockCategoryCreate(name="New Category", description="Desc")
        created_category = {"id": str(ObjectId()), "name": "New Category", "description": "Desc"}

        # Mock checks via self
        self.mock_category_repository.get_category_by_name.return_value = None # No existing category
        self.mock_category_repository.create_category.return_value = created_category

        result = service_instance.create_category(None, category_data) # db is unused

        assert result == created_category
        self.mock_category_repository.get_category_by_name.assert_called_once_with("New Category")
        self.mock_category_repository.create_category.assert_called_once_with(category_data)

    def test_create_category_already_exists(self, service_instance):
        """Test create_category when name already exists"""
        category_data = MockCategoryCreate(name="Work") # Name matches TEST_CATEGORY_1

        # Mock checks via self
        self.mock_category_repository.get_category_by_name.return_value = TEST_CATEGORY_1 # Existing category found

        result = service_instance.create_category(None, category_data) # db is unused

        assert result == TEST_CATEGORY_1 # Should return the existing one
        self.mock_category_repository.get_category_by_name.assert_called_once_with("Work")
        self.mock_category_repository.create_category.assert_not_called() # create should not be called

    # --- update_category Tests ---

    def test_update_category_success(self, service_instance):
        """Test update_category successfully"""
        category_update_data = MockCategoryUpdate(name="Updated Work Name")
        updated_category_from_repo = {"id": TEST_CATEGORY_ID_1, "name": "Updated Work Name", "description": "Work related notes"}

        # Mock checks via self
        self.mock_category_repository.get_category.return_value = TEST_CATEGORY_1 # Original category
        self.mock_category_repository.get_category_by_name.return_value = None # No conflict with new name
        self.mock_category_repository.update_category.return_value = updated_category_from_repo

        result = service_instance.update_category(None, TEST_CATEGORY_ID_1, category_update_data) # db unused

        assert result == updated_category_from_repo
        self.mock_category_repository.get_category.assert_called_once_with(TEST_CATEGORY_ID_1)
        self.mock_category_repository.get_category_by_name.assert_called_once_with("Updated Work Name")
        # Check repo update called with correct args (may need model_dump depending on repo implementation)
        self.mock_category_repository.update_category.assert_called_once_with(TEST_CATEGORY_ID_1, category_update_data)

    def test_update_category_not_found(self, service_instance):
        """Test update_category when the category to update does not exist"""
        category_update_data = MockCategoryUpdate(name="Updated Name")
        non_existent_id = str(ObjectId())

        # Mock checks via self
        self.mock_category_repository.get_category.return_value = None # Category not found

        result = service_instance.update_category(None, non_existent_id, category_update_data) # db unused

        assert result is None
        self.mock_category_repository.get_category.assert_called_once_with(non_existent_id)
        self.mock_category_repository.get_category_by_name.assert_not_called()
        self.mock_category_repository.update_category.assert_not_called()

    def test_update_category_name_conflict(self, service_instance):
        """Test update_category when the new name conflicts with another existing category"""
        category_update_data = MockCategoryUpdate(name="Personal") # Try to rename 'Work' to 'Personal'

        # Mock checks via self
        self.mock_category_repository.get_category.return_value = TEST_CATEGORY_1 # Original 'Work' category
        # Name check finds the existing 'Personal' category
        self.mock_category_repository.get_category_by_name.return_value = TEST_CATEGORY_2

        result = service_instance.update_category(None, TEST_CATEGORY_ID_1, category_update_data) # db unused

        assert result is None # Update should fail due to name conflict
        self.mock_category_repository.get_category.assert_called_once_with(TEST_CATEGORY_ID_1)
        self.mock_category_repository.get_category_by_name.assert_called_once_with("Personal")
        self.mock_category_repository.update_category.assert_not_called()

    def test_update_category_no_name_change(self, service_instance):
        """Test update_category when only description changes (no name conflict check needed)"""
        category_update_data = MockCategoryUpdate(description="Updated description") # Only description changes
        updated_category_from_repo = {"id": TEST_CATEGORY_ID_1, "name": "Work", "description": "Updated description"}

        # Mock checks via self
        self.mock_category_repository.get_category.return_value = TEST_CATEGORY_1 # Original category
        self.mock_category_repository.update_category.return_value = updated_category_from_repo

        result = service_instance.update_category(None, TEST_CATEGORY_ID_1, category_update_data) # db unused

        assert result == updated_category_from_repo
        self.mock_category_repository.get_category.assert_called_once_with(TEST_CATEGORY_ID_1)
        # Name conflict check should be skipped
        self.mock_category_repository.get_category_by_name.assert_not_called()
        self.mock_category_repository.update_category.assert_called_once_with(TEST_CATEGORY_ID_1, category_update_data)

    # --- delete_category Tests ---

    def test_delete_category_success(self, service_instance):
        """Test delete_category successfully"""
         # Mock checks via self
        self.mock_category_repository.get_category.return_value = TEST_CATEGORY_1 # Category found
        self.mock_category_repository.delete_category.return_value = True # Deletion successful in repo

        result = service_instance.delete_category(None, TEST_CATEGORY_ID_1) # db unused

        assert result == TEST_CATEGORY_1 # Returns the deleted category object
        self.mock_category_repository.get_category.assert_called_once_with(TEST_CATEGORY_ID_1)
        self.mock_category_repository.delete_category.assert_called_once_with(TEST_CATEGORY_ID_1)

    def test_delete_category_not_found(self, service_instance):
        """Test delete_category when the category does not exist"""
        non_existent_id = str(ObjectId())
        # Mock checks via self
        self.mock_category_repository.get_category.return_value = None # Category not found

        result = service_instance.delete_category(None, non_existent_id) # db unused

        assert result is None
        self.mock_category_repository.get_category.assert_called_once_with(non_existent_id)
        self.mock_category_repository.delete_category.assert_not_called()

    def test_delete_category_repo_fails(self, service_instance):
        """Test delete_category when repository deletion fails"""
        # Mock checks via self
        self.mock_category_repository.get_category.return_value = TEST_CATEGORY_1 # Category found
        self.mock_category_repository.delete_category.return_value = False # Deletion failed in repo

        result = service_instance.delete_category(None, TEST_CATEGORY_ID_1) # db unused

        assert result is None # Should return None if repo deletion fails
        self.mock_category_repository.get_category.assert_called_once_with(TEST_CATEGORY_ID_1)
        self.mock_category_repository.delete_category.assert_called_once_with(TEST_CATEGORY_ID_1)

    # --- suggest_category Tests ---

    def test_suggest_category_success_match(self, service_instance):
        """Test suggest_category when AI suggests a category present in the DB"""
        test_content = "Notes about my personal project finances"
        ai_suggestion = {
            "category": "Personal", # Matches TEST_CATEGORY_2 name
            "category_id": "some-ai-internal-id", # AI service might return its own ID
            "confidence": 0.85,
            "keywords": ["project", "finances"],
            "method": "openai"
        }

        # Mock repo and AI service via self
        self.mock_category_repository.get_categories.return_value = ALL_CATEGORIES
        self.mock_categorization_service.suggest_category.return_value = ai_suggestion

        result_category_id = service_instance.suggest_category(None, test_content) # db unused

        assert result_category_id == TEST_CATEGORY_ID_2 # Should return the DB ID
        self.mock_category_repository.get_categories.assert_called_once()
        # AI service called with empty title and the content
        self.mock_categorization_service.suggest_category.assert_called_once_with("", test_content)

    def test_suggest_category_no_match(self, service_instance):
        """Test suggest_category when AI suggests a category not present in the DB"""
        test_content = "Notes about vacation planning"
        ai_suggestion = {
            "category": "Travel", # This category is not in ALL_CATEGORIES
            "category_id": "ai-travel-id",
            "confidence": 0.9,
            "keywords": ["vacation", "planning"],
            "method": "openai"
        }

        # Mock repo and AI service via self
        self.mock_category_repository.get_categories.return_value = ALL_CATEGORIES
        self.mock_categorization_service.suggest_category.return_value = ai_suggestion

        result_category_id = service_instance.suggest_category(None, test_content) # db unused

        assert result_category_id is None # No matching category found in DB
        self.mock_category_repository.get_categories.assert_called_once()
        self.mock_categorization_service.suggest_category.assert_called_once_with("", test_content)

    def test_suggest_category_no_db_categories(self, service_instance):
        """Test suggest_category when there are no categories in the database"""
        test_content = "Some random content"

        # Mock repo (returns empty list) and AI service via self
        self.mock_category_repository.get_categories.return_value = []
        # AI service should not be called if there are no categories to match against

        result_category_id = service_instance.suggest_category(None, test_content) # db unused

        assert result_category_id is None
        self.mock_category_repository.get_categories.assert_called_once()
        self.mock_categorization_service.suggest_category.assert_not_called() # AI call skipped

    def test_suggest_category_ai_service_error(self, service_instance):
        """Test suggest_category when the underlying AI service raises an error"""
        test_content = "Content that causes AI error"
        error_message = "AI service unavailable"

        # Mock repo and AI service (to raise error) via self
        self.mock_category_repository.get_categories.return_value = ALL_CATEGORIES
        self.mock_categorization_service.suggest_category.side_effect = Exception(error_message)

        # The current implementation doesn't catch this error, so it should propagate
        with pytest.raises(Exception, match=error_message):
            service_instance.suggest_category(None, test_content) # db unused

        self.mock_category_repository.get_categories.assert_called_once()
        self.mock_categorization_service.suggest_category.assert_called_once_with("", test_content)

