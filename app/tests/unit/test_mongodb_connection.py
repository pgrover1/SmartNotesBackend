import pytest
from unittest.mock import MagicMock, patch
from bson.objectid import ObjectId

from app.db.mongodb import (
    get_client, 
    get_database, 
    get_collection, 
    get_db,
    serialize_id,
    prepare_for_mongo
)

class TestMongoDBConnection:
    """Tests for MongoDB connection handling"""

    def test_get_client(self):
        """Test get_client function"""
        # Mock MongoClient
        mock_client = MagicMock()
        mock_client.admin.command.return_value = True  # Successful ping
        
        # Mock settings
        mock_settings = MagicMock()
        mock_settings.MONGODB_URI = "mongodb://localhost:27017"
        
        with patch('app.db.mongodb.MongoClient', return_value=mock_client) as mock_mongo_client, \
             patch('app.db.mongodb.settings', mock_settings), \
             patch('app.db.mongodb._client', None):  # Ensure _client is None
            
            # Call get_client
            client = get_client()
            
            # Verify MongoClient was created with correct URI and ServerApi
            mock_mongo_client.assert_called_once()
            assert mock_mongo_client.call_args[0][0] == "mongodb://localhost:27017"
            
            # Verify ping was called
            mock_client.admin.command.assert_called_once_with('ping')
            
            # Verify client was returned
            assert client == mock_client

    def test_get_client_connection_error(self):
        """Test get_client function when connection fails"""
        # Mock MongoClient
        mock_client = MagicMock()
        mock_client.admin.command.side_effect = Exception("Connection failed")
        
        # Mock settings
        mock_settings = MagicMock()
        mock_settings.MONGODB_URI = "mongodb://localhost:27017"
        
        with patch('app.db.mongodb.MongoClient', return_value=mock_client) as mock_mongo_client, \
             patch('app.db.mongodb.settings', mock_settings), \
             patch('app.db.mongodb._client', None):  # Ensure _client is None
            
            # Call get_client and expect exception
            with pytest.raises(Exception) as excinfo:
                get_client()
            
            # Verify error message
            assert "Connection failed" in str(excinfo.value)

    def test_get_client_no_uri(self):
        """Test get_client function when MONGODB_URI is not set"""
        # Mock settings with empty URI
        mock_settings = MagicMock()
        mock_settings.MONGODB_URI = ""
        
        with patch('app.db.mongodb.settings', mock_settings), \
             patch('app.db.mongodb._client', None):  # Ensure _client is None
            
            # Call get_client and expect ValueError
            with pytest.raises(ValueError) as excinfo:
                get_client()
            
            # Verify error message
            assert "MONGODB_URI is not set" in str(excinfo.value)

    def test_get_database(self):
        """Test get_database function"""
        # Mock client
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_client.__getitem__.return_value = mock_db
        
        # Mock settings
        mock_settings = MagicMock()
        mock_settings.MONGODB_DB_NAME = "test_db"
        
        with patch('app.db.mongodb.get_client', return_value=mock_client) as mock_get_client, \
             patch('app.db.mongodb.settings', mock_settings):
            
            # Call get_database
            db = get_database()
            
            # Verify get_client was called
            mock_get_client.assert_called_once()
            
            # Verify correct database was accessed
            mock_client.__getitem__.assert_called_once_with("test_db")
            
            # Verify database was returned
            assert db == mock_db

    def test_get_collection(self):
        """Test get_collection function"""
        # Mock database
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        
        with patch('app.db.mongodb.get_database', return_value=mock_db) as mock_get_database:
            
            # Call get_collection
            collection = get_collection("test_collection")
            
            # Verify get_database was called
            mock_get_database.assert_called_once()
            
            # Verify correct collection was accessed
            mock_db.__getitem__.assert_called_once_with("test_collection")
            
            # Verify collection was returned
            assert collection == mock_collection

    def test_get_db_dependency(self):
        """Test get_db dependency function"""
        # Mock database
        mock_db = MagicMock()
        
        with patch('app.db.mongodb.get_database', return_value=mock_db) as mock_get_database:
            
            # Call get_db (it's a generator)
            db_gen = get_db()
            db = next(db_gen)
            
            # Verify get_database was called
            mock_get_database.assert_called_once()
            
            # Verify correct database was returned
            assert db == mock_db

    def test_serialize_id(self):
        """Test serialize_id function"""
        # Test with ObjectId
        object_id = ObjectId("507f1f77bcf86cd799439011")
        item = {"_id": object_id, "name": "Test Item"}
        
        serialized = serialize_id(item)
        
        # Verify _id was converted to string id
        assert "_id" not in serialized
        assert "id" in serialized
        assert serialized["id"] == "507f1f77bcf86cd799439011"
        assert serialized["name"] == "Test Item"
        
        # Test with already serialized item
        item = {"id": "507f1f77bcf86cd799439011", "name": "Test Item"}
        serialized = serialize_id(item)
        
        # Verify item remains unchanged
        assert serialized == item
        
        # Test with None
        assert serialize_id(None) is None

    def test_prepare_for_mongo(self):
        """Test prepare_for_mongo function"""
        # Test with id field
        data = {"id": 1, "name": "Test Item"}
        prepared = prepare_for_mongo(data)
        
        # Verify id was removed
        assert "id" not in prepared
        assert prepared["name"] == "Test Item"
        
        # Test without id field
        data = {"name": "Test Item", "description": "Test Description"}
        prepared = prepare_for_mongo(data)
        
        # Verify data remains unchanged
        assert prepared == data
        
        # Test with None
        assert prepare_for_mongo(None) is None