import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from bson.objectid import ObjectId

from app.repositories.base_mongodb import BaseMongoRepository
from app.db.mongodb import serialize_id, prepare_for_mongo

class TestBaseMongoRepository:
    """Tests for the BaseMongoRepository class"""

    def test_init(self):
        """Test repository initialization"""
        repo = BaseMongoRepository("test_collection")
        assert repo.collection_name == "test_collection"

    def test_get_multi(self, mock_collection, mock_mongodb_get_collection, mongodb_note_with_id, serialized_note):
        """Test get_multi method"""
        # Setup the mock collection to return a list of documents
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = [mongodb_note_with_id]
        mock_collection.find.return_value = mock_cursor
        
        # Create the repository and call get_multi
        repo = BaseMongoRepository("test_collection")
        result = repo.get_multi(skip=0, limit=10)
        
        # Verify mock collection methods were called correctly
        mock_collection.find.assert_called_once_with()
        mock_cursor.sort.assert_called_once_with("created_at", -1)
        mock_cursor.skip.assert_called_once_with(0)
        mock_cursor.limit.assert_called_once_with(10)
        
        # Verify the result is correctly serialized
        assert len(result) == 1
        assert result[0]["id"] == str(mongodb_note_with_id["_id"])
        assert result[0]["title"] == mongodb_note_with_id["title"]

    def test_get(self, mock_collection, mock_mongodb_get_collection, mongodb_note_with_id, serialized_note):
        """Test get method"""
        # Setup the mock collection to return a document
        mock_collection.find_one.return_value = mongodb_note_with_id
        
        # Create the repository and call get
        repo = BaseMongoRepository("test_collection")
        result = repo.get(str(mongodb_note_with_id["_id"]))
        
        # Verify mock collection methods were called correctly
        mock_collection.find_one.assert_called_once()
        assert mock_collection.find_one.call_args[0][0]["_id"] == mongodb_note_with_id["_id"]
        
        # Verify the result is correctly serialized
        assert result["id"] == str(mongodb_note_with_id["_id"])
        assert result["title"] == mongodb_note_with_id["title"]

    def test_get_not_found(self, mock_collection, mock_mongodb_get_collection):
        """Test get method when document not found"""
        # Setup the mock collection to return None
        mock_collection.find_one.return_value = None
        
        # Create the repository and call get
        repo = BaseMongoRepository("test_collection")
        result = repo.get("507f1f77bcf86cd799439013")
        
        # Verify the result is None
        assert result is None

    def test_get_by_filter(self, mock_collection, mock_mongodb_get_collection, mongodb_note_with_id, serialized_note):
        """Test get_by_filter method"""
        # Setup the mock collection to return a list of documents
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = [mongodb_note_with_id]
        mock_collection.find.return_value = mock_cursor
        
        # Create the repository and call get_by_filter
        repo = BaseMongoRepository("test_collection")
        filter_dict = {"title": "Test Note"}
        result = repo.get_by_filter(filter_dict, skip=0, limit=10)
        
        # Verify mock collection methods were called correctly
        mock_collection.find.assert_called_once_with(filter_dict)
        mock_cursor.sort.assert_called_once_with("created_at", -1)
        mock_cursor.skip.assert_called_once_with(0)
        mock_cursor.limit.assert_called_once_with(10)
        
        # Verify the result is correctly serialized
        assert len(result) == 1
        assert result[0]["id"] == str(mongodb_note_with_id["_id"])
        assert result[0]["title"] == mongodb_note_with_id["title"]

    def test_create(self, mock_collection, mock_mongodb_get_collection, sample_note_data, mongodb_note_with_id, serialized_note):
        """Test create method"""
        # Setup the mock collection to simulate insert_one and get
        mock_collection.insert_one.return_value = MagicMock(inserted_id=mongodb_note_with_id["_id"])
        mock_collection.find_one.return_value = mongodb_note_with_id
        
        # Create the repository and call create
        repo = BaseMongoRepository("test_collection")
        
        # Mock datetime.utcnow to ensure consistent timestamps
        with patch("app.repositories.base_mongodb.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2023, 1, 1)
            result = repo.create(sample_note_data)
        
        # Verify insert_one was called with the correct data
        assert mock_collection.insert_one.call_count == 1
        insert_data = mock_collection.insert_one.call_args[0][0]
        # Verify timestamps were added
        assert "created_at" in insert_data
        assert "updated_at" in insert_data
        
        # Verify find_one was called to get the created document
        mock_collection.find_one.assert_called_once()
        assert mock_collection.find_one.call_args[0][0]["_id"] == mongodb_note_with_id["_id"]
        
        # Verify the result is correctly serialized
        assert result["id"] == str(mongodb_note_with_id["_id"])
        assert result["title"] == mongodb_note_with_id["title"]

    def test_update(self, mock_collection, mock_mongodb_get_collection, mongodb_note_with_id, serialized_note):
        """Test update method"""
        # Setup the mock collection to simulate update_one and get
        mock_collection.update_one.return_value = MagicMock(modified_count=1)
        mock_collection.find_one.return_value = mongodb_note_with_id
        
        # Create the repository and call update
        repo = BaseMongoRepository("test_collection")
        update_data = {"title": "Updated Title"}
        
        # Mock datetime.utcnow to ensure consistent timestamps
        with patch("app.repositories.base_mongodb.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2023, 1, 2)
            result = repo.update(str(mongodb_note_with_id["_id"]), update_data)
        
        # Verify update_one was called with the correct data
        mock_collection.update_one.assert_called_once()
        assert mock_collection.update_one.call_args[0][0]["_id"] == mongodb_note_with_id["_id"]
        # Verify updated_at timestamp was added
        assert "updated_at" in mock_collection.update_one.call_args[0][1]["$set"]
        
        # Verify find_one was called to get the updated document
        mock_collection.find_one.assert_called_once()
        assert mock_collection.find_one.call_args[0][0]["_id"] == mongodb_note_with_id["_id"]
        
        # Verify the result is correctly serialized
        assert result["id"] == str(mongodb_note_with_id["_id"])
        assert result["title"] == mongodb_note_with_id["title"]

    def test_remove(self, mock_collection, mock_mongodb_get_collection):
        """Test remove method"""
        # Setup the mock collection to simulate delete_one
        mock_collection.delete_one.return_value = MagicMock(deleted_count=1)
        
        # Create the repository and call remove
        repo = BaseMongoRepository("test_collection")
        result = repo.remove("507f1f77bcf86cd799439013")
        
        # Verify delete_one was called with the correct id
        mock_collection.delete_one.assert_called_once()
        assert mock_collection.delete_one.call_args[0][0]["_id"] == ObjectId("507f1f77bcf86cd799439013")
        
        # Verify the result is True when document was deleted
        assert result is True

    def test_remove_not_found(self, mock_collection, mock_mongodb_get_collection):
        """Test remove method when document not found"""
        # Setup the mock collection to simulate delete_one with no matches
        mock_collection.delete_one.return_value = MagicMock(deleted_count=0)
        
        # Create the repository and call remove
        repo = BaseMongoRepository("test_collection")
        result = repo.remove("507f1f77bcf86cd799439013")
        
        # Verify the result is False when no document was deleted
        assert result is False

    def test_count(self, mock_collection, mock_mongodb_get_collection):
        """Test count method"""
        # Setup the mock collection to return a count
        mock_collection.count_documents.return_value = 5
        
        # Create the repository and call count
        repo = BaseMongoRepository("test_collection")
        result = repo.count()
        
        # Verify count_documents was called with empty filter
        mock_collection.count_documents.assert_called_once_with({})
        
        # Verify the result is the count
        assert result == 5

    def test_count_with_filter(self, mock_collection, mock_mongodb_get_collection):
        """Test count method with filter"""
        # Setup the mock collection to return a count
        mock_collection.count_documents.return_value = 2
        
        # Create the repository and call count with filter
        repo = BaseMongoRepository("test_collection")
        filter_dict = {"title": "Test Note"}
        result = repo.count(filter_dict)
        
        # Verify count_documents was called with the filter
        mock_collection.count_documents.assert_called_once_with(filter_dict)
        
        # Verify the result is the count
        assert result == 2