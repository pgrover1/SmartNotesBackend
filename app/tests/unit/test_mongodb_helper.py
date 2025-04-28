"""Helper utilities for mocking MongoDB in tests"""
import pytest
from unittest.mock import MagicMock, patch
from bson.objectid import ObjectId

class MockMongoDB:
    """Mock MongoDB utilities for testing"""
    
    @staticmethod
    def mock_collection():
        """Create a mock MongoDB collection"""
        mock_coll = MagicMock()
        
        # Setup commonly used methods
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = []
        
        mock_coll.find.return_value = mock_cursor
        mock_coll.find_one.return_value = None
        mock_coll.insert_one.return_value = MagicMock(inserted_id=ObjectId())
        mock_coll.update_one.return_value = MagicMock(modified_count=1)
        mock_coll.delete_one.return_value = MagicMock(deleted_count=1)
        mock_coll.count_documents.return_value = 0
        
        return mock_coll, mock_cursor
    
    @staticmethod
    def create_mock_get_collection():
        """Create a patched version of the get_collection function"""
        mock_coll, mock_cursor = MockMongoDB.mock_collection()
        
        def side_effect(collection_name):
            return mock_coll
            
        mock_get_collection = MagicMock(side_effect=side_effect)
        
        return mock_get_collection, mock_coll, mock_cursor

@pytest.fixture
def mock_mongodb_collection():
    """Fixture that returns a mock MongoDB collection"""
    mock_coll, mock_cursor = MockMongoDB.mock_collection()
    return mock_coll, mock_cursor

@pytest.fixture
def patched_get_collection():
    """Fixture that patches mongodb.get_collection"""
    mock_get_collection, mock_coll, mock_cursor = MockMongoDB.create_mock_get_collection()
    
    with patch('app.db.mongodb.get_collection', 
              side_effect=mock_get_collection) as patched:
        yield patched, mock_coll, mock_cursor