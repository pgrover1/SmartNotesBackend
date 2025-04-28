import pytest
from unittest.mock import MagicMock, patch
from bson.objectid import ObjectId

from app.repositories.category_mongodb import CategoryMongoRepository
from app.schemas.category import CategoryCreate, CategoryUpdate

class TestCategoryMongoRepository:
    """Tests for the CategoryMongoRepository class"""

    def test_init(self):
        """Test repository initialization"""
        repo = CategoryMongoRepository()
        assert repo.collection_name == "categories"

    def test_get_categories(self, mock_collection, mock_mongodb_get_collection, mongodb_category_with_id, serialized_category):
        """Test get_categories method"""
        # Setup mock for get_multi method
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = [mongodb_category_with_id]
        mock_collection.find.return_value = mock_cursor
        
        # Create the repository and call get_categories
        repo = CategoryMongoRepository()
        result = repo.get_categories(skip=0, limit=10)
        
        # Verify collection find was called
        mock_collection.find.assert_called_once_with()
        
        # Verify the result contains the expected category data
        assert len(result) == 1
        assert result[0]["id"] == str(mongodb_category_with_id["_id"])
        assert result[0]["name"] == mongodb_category_with_id["name"]

    def test_get_category(self, mock_collection, mock_mongodb_get_collection, mongodb_category_with_id, serialized_category):
        """Test get_category method"""
        # Setup mock for find_one method
        mock_collection.find_one.return_value = mongodb_category_with_id
        
        # Create the repository and call get_category
        repo = CategoryMongoRepository()
        result = repo.get_category(str(mongodb_category_with_id["_id"]))
        
        # Verify find_one was called with the correct ObjectId
        mock_collection.find_one.assert_called_once()
        assert mock_collection.find_one.call_args[0][0]["_id"] == mongodb_category_with_id["_id"]
        
        # Verify the result contains the expected category data
        assert result["id"] == str(mongodb_category_with_id["_id"])
        assert result["name"] == mongodb_category_with_id["name"]

    def test_get_category_by_name(self, mock_collection, mock_mongodb_get_collection, mongodb_category_with_id, serialized_category):
        """Test get_category_by_name method"""
        # Setup mock for get_by_filter
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = [mongodb_category_with_id]
        mock_collection.find.return_value = mock_cursor
        
        # Create the repository and call get_category_by_name
        repo = CategoryMongoRepository()
        result = repo.get_category_by_name("Test Category")
        
        # Verify find was called with the correct filter
        mock_collection.find.assert_called_once()
        assert mock_collection.find.call_args[0][0] == {"name": "Test Category"}
        
        # Verify the result contains the expected category data
        assert result["id"] == str(mongodb_category_with_id["_id"])
        assert result["name"] == "Test Category"

    def test_get_category_by_name_not_found(self, mock_collection, mock_mongodb_get_collection):
        """Test get_category_by_name when category not found"""
        # Setup mock for get_by_filter to return empty list
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = []
        mock_collection.find.return_value = mock_cursor
        
        # Create the repository and call get_category_by_name
        repo = CategoryMongoRepository()
        result = repo.get_category_by_name("Nonexistent Category")
        
        # Verify find was called with the correct filter
        mock_collection.find.assert_called_once()
        assert mock_collection.find.call_args[0][0] == {"name": "Nonexistent Category"}
        
        # Verify the result is None
        assert result is None

    def test_create_category(self, mock_collection, mock_mongodb_get_collection, serialized_category):
        """Test create_category method"""
        # Setup mocks for insert_one and find_one
        mock_collection.insert_one.return_value = MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439014"))
        mock_collection.find_one.return_value = {
            "_id": ObjectId("507f1f77bcf86cd799439014"),
            "name": "New Category",
            "description": "This is a new test category",
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        }
        
        # Create test category data
        category_create = CategoryCreate(
            name="New Category",
            description="This is a new test category"
        )
        
        # Create the repository and call create_category
        repo = CategoryMongoRepository()
        result = repo.create_category(category_create)
        
        # Verify insert_one was called
        assert mock_collection.insert_one.call_count == 1
        
        # Verify the result contains the expected category data
        assert result["id"] == "507f1f77bcf86cd799439014"
        assert result["name"] == "New Category"
        assert result["description"] == "This is a new test category"

    def test_update_category(self, mock_collection, mock_mongodb_get_collection, serialized_category):
        """Test update_category method"""
        # Setup mocks for update_one and find_one
        mock_collection.update_one.return_value = MagicMock(modified_count=1)
        mock_collection.find_one.return_value = {
            "_id": ObjectId("507f1f77bcf86cd799439014"),
            "name": "Updated Category",
            "description": "This is an updated test category",
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-02T00:00:00"
        }
        
        # Create test category update data
        category_update = CategoryUpdate(
            name="Updated Category",
            description="This is an updated test category"
        )
        
        # Create the repository and call update_category
        repo = CategoryMongoRepository()
        result = repo.update_category("507f1f77bcf86cd799439014", category_update)
        
        # Verify update_one was called with the correct data
        mock_collection.update_one.assert_called_once()
        call_args = mock_collection.update_one.call_args[0]
        assert call_args[0]["_id"] == ObjectId("507f1f77bcf86cd799439014")
        
        # Verify the updated fields are in the set operation
        set_data = call_args[1]["$set"]
        assert set_data["name"] == "Updated Category"
        assert set_data["description"] == "This is an updated test category"
        
        # Verify the result contains the expected category data
        assert result["id"] == "507f1f77bcf86cd799439014"
        assert result["name"] == "Updated Category"
        assert result["description"] == "This is an updated test category"

    def test_delete_category(self, mock_collection, mock_mongodb_get_collection):
        """Test delete_category method"""
        # Setup mock for delete_one
        mock_collection.delete_one.return_value = MagicMock(deleted_count=1)
        
        # Create the repository and call delete_category
        repo = CategoryMongoRepository()
        result = repo.delete_category("507f1f77bcf86cd799439014")
        
        # Verify delete_one was called with the correct ObjectId
        mock_collection.delete_one.assert_called_once()
        assert mock_collection.delete_one.call_args[0][0]["_id"] == ObjectId("507f1f77bcf86cd799439014")
        
        # Verify the result is True when document was deleted
        assert result is True
    
    def test_delete_category_not_found(self, mock_collection, mock_mongodb_get_collection):
        """Test delete_category when category not found"""
        # Setup mock for delete_one to return 0 deleted count
        mock_collection.delete_one.return_value = MagicMock(deleted_count=0)
        
        # Create the repository and call delete_category
        repo = CategoryMongoRepository()
        result = repo.delete_category("507f1f77bcf86cd799439014")
        
        # Verify delete_one was called with the correct ObjectId
        mock_collection.delete_one.assert_called_once()
        assert mock_collection.delete_one.call_args[0][0]["_id"] == ObjectId("507f1f77bcf86cd799439014")
        
        # Verify the result is False when no document was deleted
        assert result is False